# coding=utf-8
from typing import Literal, Optional

from graia.application import BotMessage, Friend, GraiaMiraiApplication, Group, Member
from graia.application.context import application
from graia.application.event import ApplicationDispatcher, BaseDispatcher
from graia.application.event.dispatcher import MessageChainCatcher
from graia.application.event.messages import FriendMessage, GroupMessage
from graia.application.event.mirai import MiraiEvent
from graia.application.message.chain import MessageChain
from graia.broadcast import Broadcast, DispatcherInterface
from loguru import logger


class CommandEvent(MiraiEvent):
    """
    当该事件发生时, 有用户发送了一条命令。

    当命令是本地console输入时，messageChain, user, group 皆为 None。

    **注意: 当监听该事件或该类事件时, 请优先考虑使用原始事件类作为类型注解, 以此获得事件类实例, 便于获取更多的信息!**

    Allowed Extra Parameters(提供的额外注解支持):
        GraiaMiraiApplication (annotation): 发布事件的应用实例

    :param source: 命令的来源，为 "remote" 与 "local" 之一
    :param command: 命令的字符串形式
    :param perm_lv: 命令发送者的权限等级，为一个整数
    :param msg_chain: 命令的原 MessageChain（可选）
    :param user: 发送命令的用户QQ号（可选）
    :param group: 命令发生的群组（可选）
    """

    type = "CommandEvent"
    source: str
    command: str
    perm_lv: int
    messageChain: Optional[MessageChain] = None
    user: Optional[int] = None
    group: Optional[Group] = None

    class Dispatcher(BaseDispatcher):
        mixin = [MessageChainCatcher, ApplicationDispatcher]

        @staticmethod
        async def catch(interface: "DispatcherInterface"):
            pass

    def __init__(
        self,
        source: Literal["remote", "local"],
        command: str,
        perm_lv: int,
        msg_chain: Optional[MessageChain] = None,
        user: Optional[int] = None,
        group: Optional[Group] = None,
    ):
        super().__init__(
            source=source,
            command=command,
            perm_lv=perm_lv,
            messageChain=msg_chain,
            user=user,
            group=group,
        )

    async def send_result(self, message: MessageChain) -> Optional[BotMessage]:
        """
        依据传入的参数自动发送结果至合适的端

        :param message: 要发送的消息，local端的消息会自动 asDisplay() 处理
        :return receipt: BotMessage 或 None，可用于撤回消息
        """
        app: GraiaMiraiApplication = application.get()
        if self.source == "local":
            logger.info(message.asDisplay())
            receipt = None
        elif self.group:
            receipt = await app.sendGroupMessage(self.group, message)
        else:
            receipt = await app.sendFriendMessage(self.user, message)
        return receipt

    async def get_operator(self):
        """
        返回本事件发送者的名字

        :return: 字符串，名字
        """
        app: GraiaMiraiApplication = application.get()
        if self.source == "local":
            return "Console"
        elif self.group:
            return (await app.getMember(self.group, self.user)).name
        else:
            return (await app.getFriend(self.user)).nickname


def initialize(bcc: Broadcast):
    """
    初始化 CommandEvent 的发送器

    :param bcc: Broadcast
    """

    from .control import Permission

    @bcc.receiver(GroupMessage)
    async def broadcast_command(event: GroupMessage, user: Member, group: Group):
        bcc.postEvent(
            CommandEvent(
                "remote",
                event.messageChain.asDisplay(),
                await Permission.get(user.id),
                event.messageChain,
                user.id,
                group,
            )
        )

    @bcc.receiver(FriendMessage)
    async def broadcast_command(event: FriendMessage, user: Friend):
        bcc.postEvent(
            CommandEvent(
                "remote",
                event.messageChain.asDisplay(),
                await Permission.get(user.id),
                event.messageChain,
                user.id,
            )
        )

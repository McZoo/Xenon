# coding=utf-8
from typing import Literal, Optional

from graia.application import Friend, Group, Member
from graia.application.event import EmptyDispatcher
from graia.application.event.messages import FriendMessage, GroupMessage, TempMessage
from graia.application.event.mirai import MiraiEvent
from graia.application.message.chain import MessageChain

from . import XenonContext, permission


class CommandEvent(MiraiEvent):
    """
    当该事件发生时, 有用户发送了一条命令

    ** 注意: 当监听该事件或该类事件时, 请优先考虑使用原始事件类作为类型注解, 以此获得事件类实例, 便于获取更多的信息! **

    Allowed Extra Parameters(提供的额外注解支持):
        GraiaMiraiApplication (annotation): 发布事件的应用实例
    注意：当命令是本地console输入时，msg_chain, user, group 皆为 None
    """

    type = "CommandEvent"
    source: str
    command: str
    perm_lv: int
    msg_chain: Optional[MessageChain] = None
    user: Optional[int] = None
    group: Optional[Group] = None

    Dispatcher = EmptyDispatcher

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
            msg_chain=msg_chain,
            user=user,
            group=group,
        )

    async def send_result(self, ctx: XenonContext, message: MessageChain):
        """
        依据传入的参数自动发送结果至合适的端
        :param ctx: XenonContext
        :param message: 要发送的消息，local端的消息会自动 asDisplay() 处理
        """
        if self.source == "local":
            ctx.logger.info(message.asDisplay())
        elif self.group:
            await ctx.app.sendGroupMessage(self.group, message)
        else:
            await ctx.app.sendFriendMessage(self.user, message)
        return


def initialize(ctx: XenonContext):
    """
    初始化 CommandEvent 的发送器
    :param ctx: XenonContext
    """

    @ctx.bcc.receiver(GroupMessage)
    async def broadcast_command(event: GroupMessage, user: Member, group: Group):
        ctx.bcc.postEvent(
            CommandEvent(
                "remote",
                event.messageChain.asDisplay(),
                await permission.get_perm(user.id),
                event.messageChain,
                user.id,
                group,
            )
        )

    @ctx.bcc.receiver(FriendMessage)
    async def broadcast_command(event: FriendMessage, user: Friend):
        ctx.bcc.postEvent(
            CommandEvent(
                "remote",
                event.messageChain.asDisplay(),
                await permission.get_perm(user.id),
                event.messageChain,
                user.id,
            )
        )

    @ctx.bcc.receiver(TempMessage)
    async def broadcast_command(event: TempMessage, user: Member, group: Group):
        ctx.bcc.postEvent(
            CommandEvent(
                "remote",
                event.messageChain.asDisplay(),
                await permission.get_perm(user.id),
                event.messageChain,
                user.id,
                group,
            )
        )

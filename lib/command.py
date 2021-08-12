from typing import Optional, Literal

from graia.application import Group, Member, Friend
from graia.application.event import EmptyDispatcher
from graia.application.event.messages import GroupMessage, FriendMessage, TempMessage
from graia.application.event.mirai import MiraiEvent
from graia.application.message.chain import MessageChain

from . import XenonContext, permission


class CommandEvent(MiraiEvent):
    """
    当该事件发生时, 有用户发送了一条命令

    ** 注意: 当监听该事件或该类事件时, 请优先考虑使用原始事件类作为类型注解, 以此获得事件类实例, 便于获取更多的信息! **

    Allowed Extra Parameters(提供的额外注解支持):
        GraiaMiraiApplication (annotation): 发布事件的应用实例
    注意：当命令是本地console输入时，
    """
    type = "InvokeCommand"
    source: str
    command: str
    perm_lv: int
    msg_chain: Optional[MessageChain] = None
    user: Optional[int] = None
    group: Optional[Group] = None

    Dispatcher = EmptyDispatcher

    def __init__(self, source: Literal["remote", "local"], command: str, perm_lv: int,
                 msg_chain: Optional[MessageChain] = None, user: Optional[int] = None, group: Optional[Group] = None):
        super().__init__(source=source, command=command, perm_lv=perm_lv, msg_chain=msg_chain, user=user, group=group)


def initialize(ctx: XenonContext):
    @ctx.bcc.receiver(GroupMessage)
    async def broadcast_command(event: GroupMessage, user: Member, group: Group):
        ctx.bcc.postEvent(CommandEvent("remote", event.messageChain.asDisplay(), await permission.get_perm(user.id),
                                       event.messageChain, user.id, group))

    @ctx.bcc.receiver(FriendMessage)
    async def broadcast_command(event: FriendMessage, user: Friend):
        ctx.bcc.postEvent(CommandEvent("remote", event.messageChain.asDisplay(), await permission.get_perm(user.id),
                                       event.messageChain, user.id))

    @ctx.bcc.receiver(TempMessage)
    async def broadcast_command(event: TempMessage, user: Member, group: Group):
        ctx.bcc.postEvent(CommandEvent("remote", event.messageChain.asDisplay(), await permission.get_perm(user.id),
                                       event.messageChain, user.id, group))

    @ctx.con.register()
    async def broadcast_command(command: str):
        ctx.logger.info(f'Posting command "{command}" to broadcast control.')
        ctx.logger.info("Please wait for response.")
        ctx.bcc.postEvent(CommandEvent("local", command, permission.ADMIN))

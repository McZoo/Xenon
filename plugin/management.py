import time

from graia.application import MessageChain
from graia.application.message.elements.internal import At, Plain

import lib
from lib.command import CommandEvent
from lib.permission import (
    ADMIN,
    BANNED,
    DEFAULT,
    FRIEND,
    OPERATOR,
    USER,
    get_perm,
    set_perm,
)

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(1, 0, 0),
    "management",
    "BlueGlassBlock",
    ".stop：停止 Xenon\n"
    ".set-perm USER_ID PERMISSION：设置USER_ID的权限为PERMISSION\n"
    ".query-perm USER_ID：查询USER_ID的权限",
)

_mapping = {
    "admin": ADMIN,
    "operator": OPERATOR,
    "friend": FRIEND,
    "user": USER,
    "banned": BANNED,
    "default": DEFAULT,
}


async def main(ctx: lib.XenonContext):
    @ctx.bcc.receiver(CommandEvent)
    async def stopper(event: CommandEvent):
        if event.command == ".stop" and event.perm_lv >= lib.permission.OPERATOR:
            ctx.logger.info(time.asctime())
            ctx.logger.info("Stopping Xenon...")
            if event.group:
                await ctx.app.sendGroupMessage(
                    group=event.group,
                    message=MessageChain.create(
                        [At(event.user), Plain("\n"), Plain("已停止Xenon。")]
                    ),
                )
            elif event.user:
                await ctx.app.sendFriendMessage(
                    event.user, MessageChain.create([Plain("已停止Xenon。")])
                )
            await ctx.app.shutdown()

    @ctx.bcc.receiver(CommandEvent)
    async def update_permission(event: CommandEvent):
        if (
            event.command.startswith(".set-perm")
            and len(event.command.split(" ")) == 3
            and event.perm_lv >= OPERATOR
        ):
            _, user, lv = event.command.split(" ")
            try:
                user = int(user)
                if lv.lower() in _mapping:
                    lv = _mapping[lv]
                else:
                    lv = int(lv)
            except ValueError as e:
                reply = f"无法识别参数: {e.args}"
            else:
                reply = f"设置用户 {user} 的权限为 {lv} 。"
                await set_perm(user, lv)
            if event.group:
                await ctx.app.sendGroupMessage(
                    group=event.group,
                    message=MessageChain.create(
                        [At(event.user), Plain("\n"), Plain(reply)]
                    ),
                )
            elif event.user:
                await ctx.app.sendFriendMessage(
                    event.user, MessageChain.create([Plain(reply)])
                )

    @ctx.bcc.receiver(CommandEvent)
    async def query_permission(event: CommandEvent):
        if (
            event.command.startswith(".query-perm")
            and len(event.command.split(" ")) == 2
            and event.perm_lv >= OPERATOR
        ):
            _, user = event.command.split(" ")
            try:
                user = int(user)
            except ValueError as e:
                reply = f"无法识别参数: {e.args}"
            else:
                reply = f"用户 {user} 的权限为 {await get_perm(user)} 。"
            if event.group:
                await ctx.app.sendGroupMessage(
                    group=event.group,
                    message=MessageChain.create(
                        [At(event.user), Plain("\n"), Plain(reply)]
                    ),
                )
            elif event.user:
                await ctx.app.sendFriendMessage(
                    event.user, MessageChain.create([Plain(reply)])
                )

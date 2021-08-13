import base64
from typing import TYPE_CHECKING, Optional

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At, Image

if TYPE_CHECKING:
    import mcstatus

import lib
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(lib.Version(0, 1, 0), "server_info", "BlueGlassBlock",
                                         ".server_info HOST：查询 HOST 位置服务器的状态",
                                         lib.dependency.DependencyEntry({"mcstatus": "mcstatus"}))


def main(ctx: lib.XenonContext):
    import mcstatus

    @ctx.bcc.receiver(CommandEvent)
    async def get_info(event: CommandEvent):
        if event.command.startswith('.server_info') and event.perm_lv >= lib.permission.USER:
            if len(args := event.command.split(" ")) >= 2 and event.group:
                try:
                    server = mcstatus.MinecraftServer.lookup(args[1])
                    stat = await server.async_status()
                    players: Optional[list[mcstatus.server.PingResponse.Players.Player]] = stat.players.sample
                    await ctx.app.sendGroupMessage(group=event.group, message=MessageChain.create(
                        [Plain(f"{args[1]} 状态\n"),
                         Image.fromUnsafeBytes(base64.b64decode(stat.favicon.removeprefix("data:image/png;base64,")))
                         if stat.favicon is not None else Plain(""),
                         Plain(f"玩家数：{stat.players.online}/{stat.players.max}\n"
                               f"延迟：{stat.latency}ms\n"
                               "在线玩家：\n"),
                         Plain("\n".join(i.name for i in players) if players is not None else "无"),
                         ]))
                except Exception as e:
                    await ctx.app.sendGroupMessage(group=event.group, message=MessageChain.create(
                        [At(event.user), Plain("\n"),
                         Plain(f"{e}: {e.args}"),
                         ]))

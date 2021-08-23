# coding=utf-8
import base64
from typing import Optional, List

from graia.application import MessageChain
from graia.application.message.elements.internal import Image, Plain
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

import lib
from lib.command import CommandEvent

__version__ = "1.0.0"
__plugin_name__ = "server_info"
__author__ = "BlueGlassBlock"
__dependency__ = {"mcstatus": "mcstatus"}
__plugin_doc__ = """\
.server_info HOST：查询 HOST 位置服务器的状态
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[CommandEvent]))
async def get_info(event: CommandEvent):
    if (
        event.command.startswith(".server_info")
        and event.perm_lv >= lib.permission.USER
        and len(args := event.command.split(" ")) >= 2
    ):
        import mcstatus

        try:
            server = mcstatus.MinecraftServer.lookup(args[1])
            stat = await server.async_status()
            players: Optional[
                List[mcstatus.server.PingResponse.Players.Player]
            ] = stat.players.sample
        except Exception as e:
            reply = MessageChain.create(
                [
                    Plain(f"{repr(e)}"),
                ]
            )
        else:
            reply = MessageChain.create(
                [
                    Plain(f"{args[1]} 状态\n"),
                    Image.fromUnsafeBytes(
                        base64.b64decode(
                            stat.favicon.removeprefix("data:image/png;base64,")
                        )
                    )
                    if stat.favicon is not None
                    else Plain(""),
                    Plain(
                        f"玩家数：{stat.players.online}/{stat.players.max}\n"
                        f"延迟：{stat.latency}ms\n"
                        "在线玩家：\n"
                    ),
                    Plain(
                        "\n".join(i.name for i in players)
                        if players is not None
                        else "无"
                    ),
                ]
            )
            del server, stat
        await event.send_result(reply)

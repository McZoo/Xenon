# coding=utf-8
import base64
from typing import List, Optional

from graia.application import MessageChain
from graia.application.message.elements.internal import Image, Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from lib.command import CommandEvent
from lib.control import Interval, Permission

__version__ = "1.0.0"
__plugin_name__ = "server_info"
__author__ = "BlueGlassBlock"
__dependency__ = {"mcstatus": "mcstatus"}
__usage__ = """
.server_info HOST：查询 HOST 位置服务器的状态
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".server_info")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(120.0),
        ],
    )
)
async def get_info(event: CommandEvent):
    _, server_address = event.command.split(" ", 1)
    import mcstatus

    try:
        server = mcstatus.MinecraftServer.lookup(server_address)
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
                Plain(f"{server_address} 状态\n"),
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
                    "\n".join(i.name for i in players) if players is not None else "无"
                ),
            ]
        )
        del server, stat
    await event.send_result(reply)

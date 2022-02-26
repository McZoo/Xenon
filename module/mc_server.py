from typing import List, Optional
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
import mcstatus
from graia.saya import Channel
from mcstatus.pinger import PingResponse
from graia.ariadne.message.commander.saya import CommandSchema

channel = Channel.current()

@channel.use(
    CommandSchema("[.server|服务器] {server_address:str}")
)
async def get_info(event: MessageEvent, app: Ariadne, server_address: str):
    try:
        server = mcstatus.MinecraftServer.lookup(server_address)
        stat = await server.async_status()
        players: Optional[List[PingResponse.Players.Player]] = stat.players.sample
    except Exception as e:
        reply = MessageChain.create(
            [
                Plain(f"{repr(e)}"),
            ]
        )
    else:
        reply = MessageChain(
            [
                Plain(f"{server_address} 状态\n"),
                Image(base64=stat.favicon.removeprefix("data:image/png;base64,"))
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
    await app.sendMessage(event, reply)
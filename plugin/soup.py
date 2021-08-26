# coding=utf-8
"""
毒鸡汤，StarGazer4k投稿的第一个插件
"""

import aiohttp
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from lib.command import CommandEvent
from lib.control import Permission, Interval

LIMIT = 100

__version__ = "1.0.0"
__author__ = "StarGazer4K"
__plugin_name__ = "soup"
__plugin_doc__ = f"""\
.soup 获取一碗毒鸡汤
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[CommandEvent],
                            inline_dispatchers=[Literature(".soup")],
                            headless_decorators=[Permission.require(Permission.USER),
                                                 Interval.require(30.0, 2)]))
async def soup(event: CommandEvent):
    async with aiohttp.request(
            "GET", "http://api.btstu.cn/yan/api.php"
    ) as response:
        json_str = await response.text()
    await event.send_result(MessageChain.create([Plain(json_str)]))

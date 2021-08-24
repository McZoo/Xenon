# coding=utf-8
"""
掷骰子，也可视作 Xenon 的简单示例插件
"""
import secrets

from graia.application import MessageChain, GraiaMiraiApplication
from graia.application.message.elements.internal import Plain
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema


from lib.command import CommandEvent

LIMIT = 100

__version__ = "1.0.0"
__author__ = "BlueGlassBlock"
__plugin_name__ = "dice"
__plugin_doc__ = f"""\
.dice 掷骰子，最大上限为{LIMIT}
.roll 同 .dice
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[CommandEvent]))
async def dice(app: GraiaMiraiApplication, event: CommandEvent):
    if event.user and event.command in (".dice", ".roll"):
        result = secrets.choice(range(1, LIMIT + 1))
        if event.group:
            name = (await app.getMember(event.group, event.user)).name
        elif event.user:
            name = (await app.getFriend(event.user)).nickname
        else:
            name = ""
        await event.send_result(
            MessageChain.create([Plain(f"{name} 掷骰子掷出了 {result}/{LIMIT} 点")])
        )

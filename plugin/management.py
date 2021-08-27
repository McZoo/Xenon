# coding=utf-8
import asyncio

from graia.application import MessageChain, GraiaMiraiApplication
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

import lib
from lib.command import CommandEvent
from lib.control import Permission

__version__ = "1.0.0"
__plugin_name__ = "management"
__author__ = "BlueGlassBlock"
__plugin_doc__ = """\
.stop：完全停止 Xenon
.set-perm USER_ID PERMISSION：设置USER_ID的权限为PERMISSION
.query-perm USER_ID：查询USER_ID的权限
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".stop")],
        headless_decorators=[Permission.require(Permission.OPERATOR)],
    )
)
async def stopper(app: GraiaMiraiApplication, event: CommandEvent):
    logger.info("Stopping Xenon...")
    lib.state = "STOP"
    await event.send_result(MessageChain.create([Plain("已停止Xenon。")]))
    await asyncio.sleep(1)
    saya.broadcast.loop.create_task(app.shutdown())


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".set-perm")],
        headless_decorators=[Permission.require(Permission.OPERATOR)],
    )
)
async def update_permission(event: CommandEvent):
    try:
        _, user, lv = event.command.split(" ")
        if user.startswith("@"):
            user = user.removeprefix("@")
        user = int(user)
        if lv.lower() in Permission.levels:
            lv = Permission.levels[lv.lower()]
        else:
            lv = int(lv)
    except Exception as e:
        reply = f"{repr(e)}"
    else:
        reply = f"设置用户 {user} 的权限为 {lv} 。"
        await Permission.set(user, lv)
    await event.send_result(MessageChain.create([Plain(reply)]))


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".query-perm")],
        headless_decorators=[Permission.require(Permission.OPERATOR)],
    )
)
async def query_permission(event: CommandEvent):
    try:
        _, user = event.command.split(" ")
        if user.startswith("@"):
            user = user.removeprefix("@")
        user = int(user)
    except Exception as e:
        reply = f"{repr(e)}"
    else:
        reply = f"用户 {user} 的权限为 {await Permission.get(user)} 。"
    await event.send_result(MessageChain.create([Plain(reply)]))

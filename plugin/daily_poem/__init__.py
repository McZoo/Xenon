# coding=utf-8
"""
每天推送一首古诗词
数据：https://github.com/michaelliao/shici/tree/master/web/src/main/resources/text
"""
import json
from secrets import choice

from graia.application import MessageChain
from graia.application.context import application
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler.saya import SchedulerSchema

import lib
from lib import path
from lib.command import CommandEvent

__version__ = "1.0.0"
__plugin_name__ = "daily_poem"
__author__ = "BlueGlassBlock"
__plugin_doc__ = """\
自动推送”每日诗词“至已注册的群
.poem_enable 在本群启用
.poem_disable 在本群禁用
.poem_query 查询本群历史上的今天启用状态
"""

from lib.control import Permission

saya = Saya.current()
channel = Channel.current()
db = lib.database.Database.current()
with open(path.join(path.plugin, "daily_poem", "poems.json"), "r") as data_fp:
    data = json.load(data_fp)


@channel.use(ListenerSchema(listening_events=[CommandEvent],
                            inline_dispatchers=[Literature(".poem")],
                            headless_decorators=[Permission.require(Permission.OPERATOR)]))
async def configure(event: CommandEvent):
    """
    Configure the plugin
    :param event: CommandEvent
    """
    db_cur = await db.open(
        "daily_poem_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)"
    )
    async with db_cur:
        if len(event.command.split(" ")) == 2:
            try:
                group_id = int(event.command.split(" ")[1])
            except ValueError as e:
                return await event.send_result(MessageChain.create([Plain(f"{repr(e)}")]))
        elif event.group:
            group_id = event.group.id
        else:
            return await event.send_result(MessageChain.create([Plain("无法找到群组")]))
        if event.command == ".poem_enable":
            await db_cur.insert((group_id, 1,))
            reply = "\n成功启用每日诗词"
        elif event.command == ".poem_disable":
            await db_cur.insert((group_id, 0,))
            reply = "\n成功关闭每日诗词"
        elif event.command == ".poem_query":
            res = await (
                await db_cur.select("state", (group_id,), "id = ?")
            ).fetchone()
            if res is None:
                await db_cur.insert((group_id, 0,))
                cfg: int = 0
            else:
                cfg: int = res[0]
            reply = f"\n本群的每日诗词启用状态：{bool(cfg)}"
        else:
            reply = "命令不存在！"
        await event.send_result(MessageChain.create([Plain(reply)]))


@channel.use(SchedulerSchema(lib.utils.crontab_iter("15 6 * * *")))
async def post_daily_poem():
    """
    Post content to enabled groups on 6:15
    """
    db_cur = await db.open("daily_poem_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)")
    async with db_cur:
        groups = await (await db_cur.select(id, condition="state = 1")).fetchall()
        app = application.get()
        groups = [i[0] for i in groups]
        today_poem = choice(data)
        for group in groups:
            msg = f"《{today_poem[2]}》\n{today_poem[0]}：{today_poem[1]}\n{today_poem[3]}"
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))

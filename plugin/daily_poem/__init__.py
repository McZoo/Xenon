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

saya = Saya.current()
channel = Channel.current()
db = lib.database.Database.current()
with open(path.join(path.plugin, "daily_poem", "poems.json"), "r") as data_fp:
    data = json.load(data_fp)


@channel.use(ListenerSchema(listening_events=[CommandEvent]))
async def configure(event: CommandEvent):
    """
    Configure the plugin
    :param event: CommandEvent
    """
    if (
        event.group
        and event.perm_lv >= lib.permission.OPERATOR
        and event.command in (".poem_enable", ".poem_disable", ".poem_query")
    ):
        db_cur = await db.open(
            "daily_poem_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)"
        )
        async with db_cur:
            if event.command == ".poem_enable":
                await db_cur.insert(
                    (
                        event.group.id,
                        1,
                    )
                )
                reply = "\n成功启用每日诗词"
            elif event.command == ".poem_disable":
                await db_cur.insert(
                    (
                        event.group.id,
                        0,
                    )
                )
                reply = "\n成功关闭每日诗词"
            elif event.command == ".poem_query":
                res = await (
                    await db_cur.select("state", (event.group.id,), "id = ?")
                ).fetchone()
                if res is None:
                    await db_cur.execute(
                        "INSERT INTO daily_poem_cfg VALUES (?, ?)", (event.group, 0)
                    )
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
            msg = f"{today_poem[2]}——{today_poem[0]}：{today_poem[1]}\n{today_poem[3]}"
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))

# coding=utf-8
"""
history of today plugin
"""
import json
from datetime import datetime

from graia.application import MessageChain
from graia.application.context import application
from graia.application.message.elements.internal import At, Plain
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler.saya import SchedulerSchema

import lib
from lib import path
from lib.command import CommandEvent

__version__ = "1.0.0"
__plugin_name__ = "history_today"
__author__ = "BlueGlassBlock"
__plugin_doc__ = """\
    "自动推送”历史上的今天“至已注册的群\n"
    ".history_enable 在本群启用\n"
    ".history_disable 在本群禁用\n"
    ".history_query 查询本群历史上的今天启用状态",
"""

saya = Saya.current()
channel = Channel.current()
db = lib.database.Database.current()
with open(path.join(path.plugin, "history_today", "history.json"), "r") as data_fp:
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
        and event.command in (".history_enable", ".history_disable", ".history_query")
    ):
        db_cur = await db.open(
            "history_today_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)"
        )
        async with db_cur:
            if event.command == ".history_enable":
                await db_cur.execute(
                    "INSERT INTO history_today_cfg VALUES (?, ?) "
                    "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                    (
                        event.group.id,
                        1,
                    ),
                )
                reply = "\n成功启用历史上的今天"
            elif event.command == ".history_disable":
                await db_cur.execute(
                    "INSERT INTO history_today_cfg VALUES (?, ?) "
                    "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                    (
                        event.group.id,
                        0,
                    ),
                )
                reply = "\n成功关闭历史上的今天"
            elif event.command == ".history_query":
                res = await (
                    await db_cur.execute(
                        "SELECT state FROM history_today_cfg where id = ?",
                        (event.group.id,),
                    )
                ).fetchone()
                if res is None:
                    await db_cur.execute(
                        "INSERT INTO history_today_cfg VALUES (?, ?)", (event.group, 0)
                    )
                    cfg: int = 0
                else:
                    cfg: int = res[0]
                reply = f"\n本群的历史上的今天启用状态：{bool(cfg)}"
            else:
                reply = "命令不存在！"
            await event.send_result(MessageChain.create([At(event.user), Plain(reply)]))


@channel.use(SchedulerSchema(lib.utils.crontab_iter("15 6 * * *")))
async def post_history_today():
    """
    Post content to enabled groups on 6:30
    """
    db_cur = await db.open(
        "history_today_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)"
    )
    async with db_cur:
        curr_time = datetime.now()
        groups = await (
            await db_cur.execute("select id FROM history_today_cfg WHERE state = 1")
        ).fetchall()
        groups = [i[0] for i in groups]
        app = application.get()
        for group in groups:
            entries = data[str(curr_time.month)][str(curr_time.day)]["data"]
            msg = (
                f"今天是{curr_time.year}年{curr_time.month}月{curr_time.day}日\n"
                + (
                    f"{data[str(curr_time.month)][str(curr_time.day)]['festival']}\n"
                    if data[str(curr_time.month)][str(curr_time.day)]["festival"]
                    else ""
                )
                + "\n".join(f"{e[0]}年，{e[1]}" for e in entries)
            )
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))

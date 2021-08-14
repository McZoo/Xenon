import json
from datetime import datetime

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At

import lib
from lib import path
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(lib.Version(0, 1, 0), "history_today", "BlueGlassBlock",
                                         "自动推送”历史上的今天“至已注册的群\n"
                                         ".history_enable 在本群启用\n"
                                         ".history_disable 在本群禁用\n", lib.dependency.DependencyEntry({"PIL": "pillow"}))


async def main(ctx: lib.XenonContext):
    db_cur = await lib.database.open_db("history_today_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)")
    data_fp = open(path.join(path.plugin, "history_today", "data.json"), "r")
    data = json.load(data_fp)

    @ctx.bcc.receiver(CommandEvent)
    async def set_config(event: CommandEvent):
        if event.group and event.perm_lv >= lib.permission.OPERATOR and \
                event.command in ('.history_enable', '.history_disable', '.history_query'):
            if event.command == ".history_enable":
                await db_cur.execute("INSERT INTO history_today_cfg VALUES (?, ?) "
                                     "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                                     (event.group.id, 1,))
                reply = "成功启用历史上的今天"
            elif event.command == ".history_disable":
                await db_cur.execute("INSERT INTO history_today_cfg VALUES (?, ?) "
                                     "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                                     (event.group.id, 0,))
                reply = "成功关闭历史上的今天"
            elif event.command == ".history_query":
                res = await (await db_cur.execute("SELECT pref FROM history_today_cfg where id = ?",
                                                  (event.group.id,))).fetchone()
                if res is None:
                    await db_cur.execute("INSERT INTO history_today_cfg VALUES (?, ?)", (event.group, 0))
                    cfg: int = 0
                else:
                    cfg: int = res[0]
                reply = f"本群的历史上的今天启用状态：{bool(cfg)}"
            else:
                reply = "命令不存在！"
            await ctx.app.sendGroupMessage(event.group, MessageChain.create([At(event.user), Plain(reply)]))

    @ctx.scheduler.schedule(lib.utils.crontab_iter("21 23 * * *"))
    async def post_history_today():
        curr_time = datetime.now()
        groups = await (await db_cur.execute("select id FROM history_today_cfg WHERE state = 1")).fetchall()
        groups = [i[0] for i in groups]
        for group in groups:
            entries = data[curr_time.month][curr_time.day]
            msg = '\n'.join(f'{e[0]}.{curr_time.month}.{curr_time.day}，{e[1]}' for e in entries)
            await ctx.app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))

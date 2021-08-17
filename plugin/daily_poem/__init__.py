"""
每天推送一首古诗词
数据：https://github.com/michaelliao/shici/tree/master/web/src/main/resources/text
"""
import json
from secrets import choice

from graia.application import MessageChain
from graia.application.message.elements.internal import At, Plain

import lib
from lib import path
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(1, 0, 0),
    "daily_poem",
    "BlueGlassBlock",
    "自动推送”每日诗词“至已注册的群\n"
    ".poem_enable 在本群启用\n"
    ".poem_disable 在本群禁用\n"
    ".poem_query 查询本群历史上的今天启用状态",
)


async def main(ctx: lib.XenonContext):
    """
    the main of the plugin
    :param ctx: XenonContext
    """
    db_cur = await lib.database.open_db(
        "daily_poem_cfg", "(id INTEGER PRIMARY KEY, state INTEGER)"
    )
    data_fp = open(path.join(path.plugin, "daily_poem", "poems.json"), "r")
    data = json.load(data_fp)
    data_fp.close()

    @ctx.bcc.receiver(CommandEvent)
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
            if event.command == ".poem_enable":
                await db_cur.execute(
                    "INSERT INTO daily_poem_cfg VALUES (?, ?) "
                    "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                    (
                        event.group.id,
                        1,
                    ),
                )
                reply = "\n成功启用每日诗词"
            elif event.command == ".poem_disable":
                await db_cur.execute(
                    "INSERT INTO daily_poem_cfg VALUES (?, ?) "
                    "ON CONFLICT (id) DO UPDATE SET state = excluded.state",
                    (
                        event.group.id,
                        0,
                    ),
                )
                reply = "\n成功关闭每日诗词"
            elif event.command == ".poem_query":
                res = await (
                    await db_cur.execute(
                        "SELECT state FROM daily_poem_cfg where id = ?",
                        (event.group.id,),
                    )
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
            await ctx.app.sendGroupMessage(
                event.group, MessageChain.create([At(event.user), Plain(reply)])
            )

    @ctx.scheduler.schedule(lib.utils.crontab_iter("15 6 * * *"))
    async def post_daily_poem():
        """
        Post content to enabled groups on 6:15
        """
        groups = await (
            await db_cur.execute("select id FROM daily_poem_cfg WHERE state = 1")
        ).fetchall()
        groups = [i[0] for i in groups]
        today_poem = choice(data)
        for group in groups:
            msg = f"{today_poem[2]}——{today_poem[0]}：{today_poem[1]}\n{today_poem[3]}"
            await ctx.app.sendGroupMessage(group, MessageChain.create([Plain(msg)]))

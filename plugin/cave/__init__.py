# coding=utf-8
"""
Xenon
回声洞
灵感来源于PCL2内测群
"""
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

import lib
from lib import permission
from lib.command import CommandEvent
from .entry_parser import to_list, to_text

__version__ = "2.0.0"
__plugin_name__ = "cave"
__author__ = "BlueGlassBlock"
__plugin_doc__ = """\
回声洞（不要与PCL2的回声洞混淆了！）
.cave： 从回声洞抽取一条语录
.cave-a MESSAGE： 向回声洞添加一条语录
.cave-v ID：查看回声洞指定ID的语录
.cave-d ID：删除回声洞指定ID的语录
.cave-s CONTENT: 在回声洞中搜索 CONTENT
.cave-count：统计回声洞条数"""

saya = Saya.current()
channel = Channel.current()
db = lib.database.Database.current()


@channel.use(ListenerSchema(listening_events=[CommandEvent]))
async def cave(event: CommandEvent):
    if event.command == ".cave" and event.perm_lv >= permission.USER:
        db_cur = await db.open(
            "cave", "(id INTEGER PRIMARY KEY, name TEXT, message TEXT)"
        )
        async with db_cur:
            entry = await (
                await db_cur.select("*", order_by="RANDOM() DESC", extra="LIMIT 1")
            ).fetchone()
            msg = f"回声洞 #{entry[0]} by {entry[1]}\n"
            await event.send_result(await to_list(entry[2], [Plain(msg)]))


@channel.use(ListenerSchema(listening_events=[CommandEvent]))
async def cave_mgmt(event: CommandEvent):
    if event.command.startswith(".cave-") and event.perm_lv >= permission.FRIEND:
        db_cur = await db.open(
            "cave", "(id INTEGER PRIMARY KEY, name TEXT, message TEXT)"
        )
        async with db_cur:
            cmd = event.command.removeprefix(".cave-")
            if cmd.startswith("a "):
                row = await (
                    await db_cur.select(
                        "MIN(id) +1",
                        condition="id + 1 NOT IN (SELECT id FROM cave)",
                    )
                ).fetchone()
                msg_id = row[0]
                if msg_id is None:
                    msg_id = 1
                if event.source == "remote":
                    chain = event.msg_chain.asSendable().asMerged()
                else:
                    chain = MessageChain.create([Plain(event.command)])
                await db_cur.insert(
                    (
                        msg_id,
                        await event.get_operator(),
                        await to_text(chain[(0, len(".cave-a ")) :]),
                    ),
                )
                reply = MessageChain.create([Plain(f"成功添加，ID为{msg_id}")])
            elif cmd.startswith("d "):
                try:
                    target_id = int(cmd.removeprefix("d "))
                    res = await (
                        await db_cur.select("*", (target_id,), "id = ?")
                    ).fetchone()
                    if not res:
                        raise ValueError(f"#{target_id}不存在")
                except ValueError as e:
                    reply = MessageChain.create([Plain(f"内容错误：{e.args}")])
                else:
                    await db_cur.delete((target_id,), "id = ?")
                    reply = await to_list(res[2], [Plain(f"已删除#{target_id}：")])
            elif cmd.startswith("v "):
                try:
                    target_id = int(cmd.removeprefix("v "))
                    res = await (
                        await db_cur.select("*", (target_id,), "id = ?")
                    ).fetchone()
                    if not res:
                        raise ValueError(f"#{target_id}不存在")
                except ValueError as e:
                    reply = MessageChain.create([Plain(f"内容错误：{e.args}")])
                else:
                    reply = await to_list(res[2], [Plain(f"#{target_id} by {res[1]}：")])
            elif cmd.startswith("s "):
                target = cmd.removeprefix("s ")
                msg = await (
                    await db_cur.select("id", condition=f"message LIKE '%{target}%'")
                ).fetchall()
                name = await (
                    await db_cur.select("id", condition=f"name LIKE '%{target}%'")
                ).fetchall()
                final_res = set(i[0] for i in msg) | set(i[0] for i in name)  # merge id
                reply = MessageChain.create(
                    [
                        Plain(f"共找到{len(final_res)}条记录：\n"),
                        Plain("，".join(f"#{i}" for i in final_res)),
                    ]
                )
            elif cmd == "count":
                cnt = await ((await db_cur.select("COUNT()")).fetchone())
                reply = MessageChain.create([Plain(f"Xenon 回声洞：\n共有{cnt[0]}条记录")])
            else:
                reply = MessageChain.create([Plain("命令无效")])
            await event.send_result(reply)

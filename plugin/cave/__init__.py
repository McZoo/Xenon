"""
Xenon
回声洞
灵感来源于PCL2内测群
"""
from graia.application import Member, MessageChain
from graia.application.message.elements.internal import Plain

import lib
from lib import permission
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 1, 0),
    "cave",
    "BlueGlassBlock",
    "回声洞（不要与PCL2的回声洞混淆了！）\n"
    "注：回声洞当前只支持文字\n"
    ".cave： 从回声洞抽取一条语录\n"
    ".cave-a MESSAGE： 向回声洞添加一条语录\n"
    ".cave-v ID：查看回声洞指定ID的语录\n"
    ".cave-d ID：删除回声洞指定ID的语录\n"
    ".cave-count：查看回声洞状态",
)


async def main(ctx: lib.XenonContext):
    """
    主函数
    :param ctx: XenonContext
    :return: None
    """
    db_cur = await lib.database.open_db(
        "cave", "(id INTEGER PRIMARY KEY, name TEXT, message TEXT)"
    )

    @ctx.bcc.receiver(CommandEvent)
    async def cave(event: CommandEvent):
        if (
            event.command == ".cave"
            and event.perm_lv >= permission.USER
            and event.group
        ):
            entry = await (
                await db_cur.execute(
                    "SELECT * FROM cave" " ORDER BY RANDOM() DESC LIMIT 1"
                )
            ).fetchone()
            msg = f"回声洞 #{entry[0]} by {entry[1]}\n{entry[2]}"
            await ctx.app.sendGroupMessage(
                event.group, MessageChain.create([Plain(msg)])
            )

    @ctx.bcc.receiver(CommandEvent)
    async def cave_mgmt(event: CommandEvent):
        if (
            event.command.startswith(".cave-")
            and event.group
            and event.perm_lv >= permission.FRIEND
        ):
            cmd = event.command.removeprefix(".cave-")
            if cmd.startswith("a "):
                member: Member = await ctx.app.getMember(event.group, event.user)
                msg_id = (
                    await (await db_cur.execute("SELECT MAX(id) FROM cave")).fetchone()
                )[0]
                msg_id = 0 if msg_id is None else msg_id
                msg_id += 1
                await db_cur.execute(
                    "INSERT INTO cave VALUES (?, ?, ?)",
                    (msg_id, member.name, cmd.removeprefix("a ")),
                )
                reply = f"成功添加，ID为{msg_id}"
            elif cmd.startswith("d "):
                try:
                    target_id = int(cmd.removeprefix("d "))
                    res = await (
                        await db_cur.execute(
                            "SELECT * FROM cave WHERE id = ?", (target_id,)
                        )
                    ).fetchone()
                    if not res:
                        raise ValueError(f"#{target_id}不存在")
                except ValueError as e:
                    reply = f"内容错误：{e.args}"
                else:
                    await db_cur.execute("DELETE FROM cave WHERE id = ?", (target_id,))
                    reply = f"已删除#{target_id}：{res[2]}"
            elif cmd.startswith("v "):
                try:
                    target_id = int(cmd.removeprefix("v "))
                    res = await (
                        await db_cur.execute(
                            "SELECT * FROM cave WHERE id = ?", (target_id,)
                        )
                    ).fetchone()
                    if not res:
                        raise ValueError(f"#{target_id}不存在")
                except ValueError as e:
                    reply = f"内容错误：{e.args}"
                else:
                    reply = f"#{target_id}：{res[2]}"
            elif cmd == "count":
                cnt = await (
                    (await db_cur.execute("SELECT COUNT() FROM cave")).fetchone()
                )
                reply = f"Xenon 回声洞：\n共有{cnt[0]}条记录"
            else:
                reply = "命令无效"
            await ctx.app.sendGroupMessage(
                event.group, MessageChain.create([Plain(reply)])
            )

from graia.application import MessageChain
from graia.application.message.elements.internal import At, Plain

import lib
from lib import permission
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 1, 0),
    "about",
    "BlueGlassBlock",
    ".help： Xenon 的帮助菜单\n" ".about： 关于Xenon的信息",
)


async def main(ctx: lib.XenonContext):
    @ctx.bcc.receiver(CommandEvent)
    async def about(event: CommandEvent):
        if (
            event.user
            and event.perm_lv >= permission.USER
            and event.command.startswith(".about")
        ):
            reply = (
                f"Xenon {lib.__version__} by McZoo\n"
                f"已加载{len(ctx.plugins.loaded)}个插件。\n"
                f"有{len(ctx.plugins.unloaded) + len(ctx.plugins.broken)}个插件失效。\n"
                "需要更多帮助？请使用 .help 命令。"
            )
            if event.group:
                await ctx.app.sendGroupMessage(
                    group=event.group,
                    message=MessageChain.create(
                        [At(event.user), Plain("\n"), Plain(reply)]
                    ),
                )
            elif event.user:
                await ctx.app.sendFriendMessage(
                    event.user, MessageChain.create([Plain(reply)])
                )

    @ctx.bcc.receiver(CommandEvent)
    async def xenon_help(event: CommandEvent):
        if (
            event.user
            and event.perm_lv >= permission.USER
            and event.command.startswith(".help")
        ):
            if (
                len(event.command.split()) == 2
                and (name := event.command.split()[1]) in ctx.plugins.loaded.keys()
            ):
                spec = ctx.plugins.loaded[name].plugin_spec
                reply_list = [
                    "Xenon 帮助： ",
                    f"{name} by {spec.author}",
                    f"版本：{spec.version}",
                    f"依赖项：{spec.depend.names}",
                    spec.doc_string,
                ]
            else:
                reply_list = ["Xenon 帮助"]
                reply_list.extend(ctx.plugins.loaded.keys())
                reply_list.append(f"共{len(ctx.plugins.loaded.keys())}个加载的插件。")
                reply_list.append("请使用.help PLUGIN 查询 PLUGIN 下的帮助。")
            reply = "\n".join(reply_list)
            if event.group:
                await ctx.app.sendGroupMessage(
                    group=event.group,
                    message=MessageChain.create(
                        [At(event.user), Plain("\n"), Plain(reply)]
                    ),
                )
            elif event.user:
                await ctx.app.sendFriendMessage(
                    event.user, MessageChain.create([Plain(reply)])
                )

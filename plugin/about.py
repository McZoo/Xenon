# coding=utf-8
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

import lib
from lib.command import CommandEvent
from lib.control import Permission, Interval
from lib.plugin import PluginContainer

__version__ = "1.0.0"
__plugin_name__ = "about"
__author__ = "BlueGlassBlock"
__plugin_doc__ = """\
.help： Xenon 的帮助菜单
.about： 关于Xenon的信息
"""

saya = Saya.current()
channel = Channel.current()
plugins: PluginContainer = PluginContainer.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".about")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(30.0, 2),
        ],
    )
)
async def about(event: CommandEvent):
    reply = MessageChain.create(
        [
            Plain(
                f"Xenon {lib.__version__} by McZoo\n"
                f"已加载{len(plugins.loaded)}个插件。\n"
                f"有{len(plugins.unloaded) + len(plugins.broken)}个插件失效。\n"
                "需要更多帮助？请使用 .help 命令。"
            )
        ]
    )
    await event.send_result(reply)


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".help")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(30.0, 2),
        ],
    )
)
async def xenon_help(event: CommandEvent):
    if len(event.command.split()) == 2:
        name = event.command.split()[1]
        if name in plugins.loaded.keys():
            spec = plugins.loaded[name].spec
            reply_list = [
                "Xenon 帮助： ",
                f"{name} by {spec.author}" if spec.author else f"{name}",
                f"版本：{spec.version}" if spec.version else "",
                f"依赖项：{list(i.name for i in spec.dependency)}"
                if spec.dependency
                else "",
                spec.doc,
            ]
        else:
            reply_list = [f"插件{name}不存在"]
    else:
        reply_list = ["Xenon 帮助"]
        reply_list.extend(p for p in plugins.loaded.keys())
        reply_list.append(f"共{len(plugins.loaded)}个加载的插件。")
        reply_list.append("请使用.help PLUGIN 查询 PLUGIN 下的帮助。")
    reply = "\n".join(reply_list)
    await event.send_result(MessageChain.create([Plain(reply)]))

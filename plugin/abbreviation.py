# coding=utf-8
"""
命令映射
"""
import shlex
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from lib.command import CommandEvent
from lib.config import XenonConfig
from lib.control import Permission


class AbbreviationConfig(XenonConfig):
    restricted: List[str] = [".set_abbr", ".del_abbr", ".query_abbr"]
    mapping: Dict[str, str] = {}
    name: str = "abbr"

    def get_literature(self) -> List[Literature]:
        return [Literature(x) for x in self.mapping]


__version__ = "1.0.0"
__author__ = "BlueGlassBlock"
__plugin_name__ = "abbreviation"
__usage__ = """
.set_abbr A B 将 A 的缩写设置为 B
.del_abbr A 删除关于 A 的缩写
.query_abbr 查询所有缩写（慎用！）
"""

saya = Saya.current()
channel = Channel.current()

config = AbbreviationConfig.get_config()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".set_abbr")],
        headless_decorators=[
            Permission.require(Permission.MODERATOR),
        ],
    )
)
async def set_abbr(event: CommandEvent):
    try:
        args = shlex.split(event.command)
        map_pattern: str = args[1].strip(" ")
        ptr_pattern: str = args[2].strip(" ")
        if map_pattern in config.restricted + [".set_abbr", ".del_abbr", ".query_abbr"]:
            raise KeyError(f"不可使用 {map_pattern}！")
        if map_pattern == ptr_pattern:
            raise ValueError(f"映射不可与来源相同！")
        config.mapping[map_pattern] = ptr_pattern
        config.write()
        await event.send_result(
            MessageChain.create([Plain(f"成功设置 {ptr_pattern}" f" 的缩写为 {map_pattern}")])
        )
    except Exception as e:
        logger.exception(e)
        await event.send_result(MessageChain.create([Plain(repr(e))]))


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".del_abbr")],
        headless_decorators=[
            Permission.require(Permission.MODERATOR),
        ],
    )
)
async def del_abbr(event: CommandEvent):
    try:
        args = shlex.split(event.command)
        pattern: str = args[1].strip(" ")
        del config.mapping[pattern]
        config.write()
        await event.send_result(MessageChain.create([Plain(f"成功删除 {pattern} 的缩写")]))
    except Exception as e:
        logger.exception(e)
        await event.send_result(MessageChain.create([Plain(repr(e))]))


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".query_abbr")],
        headless_decorators=[
            Permission.require(Permission.MODERATOR),
        ],
    )
)
async def query_all_abbr(event: CommandEvent):
    entries: DefaultDict[str, Set[str]] = defaultdict(set)
    for key, val in config.mapping.items():
        entries[val].add(key)
    reply = [f"被禁用的缩写：{config.restricted}", f"缩写："]
    for string, mapping in entries.items():
        reply.append(f"{mapping} -> {repr(string)}")
    await event.send_result(MessageChain.create([Plain("\n".join(reply))]))


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        headless_decorators=[
            Permission.require(Permission.USER),
        ],
    )
)
async def repost(event: CommandEvent):
    for x in config.get_literature():
        res: Optional[MessageChain] = x.prefix_match(event.messageChain.asSendable())
        if res:
            new_chain = MessageChain.create(
                [
                    Plain(
                        config.mapping[x.prefixs[0]]
                        + (" " if len(res.__root__) else "")
                    )
                ]
            )
            new_chain.plus(res)
            final_chain = new_chain.asMerged()
            saya.broadcast.postEvent(
                CommandEvent(
                    event.source, event.perm_lv, final_chain, event.user, event.group
                )
            )

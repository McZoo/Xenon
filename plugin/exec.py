# coding=utf-8
"""
命令执行器
"""

import builtins
import traceback
from asyncio import AbstractEventLoop
from io import StringIO
from typing import Any, Dict

from graia.application import GraiaMiraiApplication, MessageChain
from graia.application.message.elements.internal import Plain
from graia.application.message.parser.literature import Literature
from graia.broadcast import Broadcast
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from lib.command import CommandEvent
from lib.control import Permission

__version__ = "1.0.0"
__author__ = "BlueGlassBlock"
__plugin_name__ = "exec"
__usage__ = """
.profile_info 查看本地环境信息
.new_profile ID 新建本地变量环境
.del_profile ID 删除本地变量环境
.exec ID [NEWLINE] EXPRESSIONS 在 #ID 中执行 EXPRESSIONS
"""

saya = Saya.current()
channel = Channel.current()


class InvalidProfileId(Exception):
    pass


class ProfileManager:
    profile: Dict[int, dict] = {}
    app: GraiaMiraiApplication
    bcc: Broadcast
    loop: AbstractEventLoop
    ready: bool = False
    print_io: StringIO = StringIO()

    @classmethod
    def init(cls, app: GraiaMiraiApplication):
        cls.ready = True
        cls.app = app
        cls.bcc = app.broadcast
        cls.loop = cls.bcc.loop
        cls.new_profile(1)

    @classmethod
    def print(cls, *args, **kwargs):
        builtins.print(*args, **kwargs, file=cls.print_io)

    @classmethod
    def new_profile(cls, id: int):
        cls.profile[id] = {
            "app": cls.app,
            "bcc": cls.bcc,
            "loop": cls.loop,
            "print": cls.print,
        }

    @classmethod
    def del_profile(cls, id: int):
        if id in cls.profile:
            del cls.profile[id]

    @classmethod
    def execute(cls, id: int, expr: str) -> Any:
        if id not in cls.profile:
            raise InvalidProfileId(f"Unable to find profile #{id}")
        return exec(expr, globals(), cls.profile[id])


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".exec")],
        headless_decorators=[
            Permission.require(Permission.ADMIN),
        ],
    )
)
async def execute_command(app: GraiaMiraiApplication, event: CommandEvent):
    if not ProfileManager.ready:
        ProfileManager.init(app)
    try:
        _, profile_id, cmd_real = event.command.split(None, 2)
        ProfileManager.execute(int(profile_id), cmd_real)
    except InvalidProfileId as e:
        await event.send_result(MessageChain.create([Plain(e.args[0])]))
    except Exception as e:
        exception_str_io = StringIO()
        traceback.print_exc(limit=5, file=exception_str_io)
        await event.send_result(
            MessageChain.create(
                [Plain(f"! An exception occurred:\n{exception_str_io.getvalue()}")]
            )
        )
        exception_str_io.close()
    else:
        if result := ProfileManager.print_io.getvalue():
            await event.send_result(
                MessageChain.create([Plain(f"Run result:\n{result}")])
            )
            ProfileManager.print_io.truncate(0)
        else:
            await event.send_result(MessageChain.create([Plain(f"Run complete.")]))


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".new_profile")],
        headless_decorators=[
            Permission.require(Permission.ADMIN),
        ],
    )
)
async def new_profile(app: GraiaMiraiApplication, event: CommandEvent):
    if not ProfileManager.ready:
        ProfileManager.init(app)
    try:
        _, profile_id, *_ = event.command.split(" ")
        ProfileManager.new_profile(int(profile_id))
    except Exception as e:
        await event.send_result(MessageChain.create([Plain(repr(e))]))
    else:
        await event.send_result(
            MessageChain.create([Plain(f"Successfully created #{profile_id}")])
        )


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".del_profile")],
        headless_decorators=[
            Permission.require(Permission.ADMIN),
        ],
    )
)
async def del_profile(app: GraiaMiraiApplication, event: CommandEvent):
    if not ProfileManager.ready:
        ProfileManager.init(app)
    try:
        _, profile_id, *_ = event.command.split(" ")
        ProfileManager.del_profile(int(profile_id))
    except Exception as e:
        await event.send_result(MessageChain.create([Plain(repr(e))]))
    else:
        await event.send_result(
            MessageChain.create([Plain(f"Successfully deleted #{profile_id}")])
        )


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".profile_info")],
        headless_decorators=[
            Permission.require(Permission.ADMIN),
        ],
    )
)
async def profile_info(app: GraiaMiraiApplication, event: CommandEvent):
    if not ProfileManager.ready:
        ProfileManager.init(app)
    profile_info = f"Total: {len(ProfileManager.profile)} profiles:\n {' '.join(f'#{index}' for index in ProfileManager.profile)}"
    await event.send_result(MessageChain.create([Plain(profile_info)]))

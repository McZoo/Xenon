from graia.application import MessageChain
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from lib.command import CommandEvent
from lib.control import Interval, Permission

LIMIT = 100

__version__ = "1.0.0"
__author__ = "Test"
__plugin_name__ = "test"
usage = """
.test
"""

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".test")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(30.0),
        ],
    )
)
async def auto(event: CommandEvent):
    if event.source == "friend":
        li = event.messageChain.__root__[1:]
        await event.send_result(MessageChain.create(li))

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.ariadne.message.commander import Commander
from graia.ariadne.message.commander.saya import CommanderBehaviour
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya.behaviour import GraiaSchedulerBehaviour
from prompt_toolkit.styles.style import Style
from pydantic.networks import AnyHttpUrl

import module
from library import __version__ as lib_version
from library.config import XConfig


class SessionConfig(XConfig):
    __scope__: str = "session"
    __dest__: str = "global"
    host: AnyHttpUrl
    account: int
    verify_key: str


if __name__ == """__main__""":
    ariadne = Ariadne(MiraiSession(**SessionConfig().dict()))
    saya = ariadne.create(Saya)
    con = ariadne.create(Console)
    con.l_prompt = f"Xenon {lib_version} > "
    con.style = Style([("", "blue")])
    ariadne.create(GraiaScheduler)
    ariadne.create(Commander)
    saya.install_behaviours(
        ariadne.create(BroadcastBehaviour),
        ariadne.create(GraiaSchedulerBehaviour),
        ariadne.create(ConsoleBehaviour),
        ariadne.create(CommanderBehaviour),
    )
    with saya.module_context():
        for mod in module.__all__:
            saya.require(f"module.{mod}")
    ariadne.launch_blocking()

"""
The base file of Xenon library, provides `Version` class as global
"""
import asyncio
import dataclasses
from typing import TYPE_CHECKING

from graia.application import GraiaMiraiApplication
from graia.broadcast import Broadcast

if TYPE_CHECKING:
    # only for type checking because we don't want `Version` class to be used before its declaration in __init__.py
    from . import path, log, console, config, database, dependency, plugin, utils, permission, command


@dataclasses.dataclass(repr=False, order=True, frozen=True)
class Version:
    """
    Version object implementation
    """
    major: int = 0
    minor: int = 0
    micro: int = 0
    serial: str = "exp"

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.micro}-{self.serial}'

    def __repr__(self):
        return f'<Version {self.__str__()}>'


__version__ = Version(0, 2, 0, "exp")  # check before new version rollout


@dataclasses.dataclass
class XenonContext:
    con: "console.Console"
    logger: "log.Logger"
    plugins: "plugin.XenonPluginList"
    loop: "asyncio.AbstractEventLoop"
    app: "GraiaMiraiApplication"
    bcc: "Broadcast"


if not TYPE_CHECKING:  # real importing work
    from . import path, log, config
    from . import dependency, plugin, utils, database
    from . import permission, command, console

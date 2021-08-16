"""
The base file of Xenon library, provides `Version` class as global
"""
import asyncio
import dataclasses
from typing import TYPE_CHECKING

from graia.application import GraiaMiraiApplication
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler

if TYPE_CHECKING:
    # only for type checking
    # because we don't want `Version` class to be used before its declaration in __init__.py
    from . import (
        command,
        config,
        console,
        database,
        dependency,
        log,
        path,
        permission,
        plugin,
        utils,
    )


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
        return f"{self.major}.{self.minor}.{self.micro}-{self.serial}"

    def __repr__(self):
        return f"<Version {self.__str__()}>"


__version__ = Version(minor=2, micro=4)  # check before new version rollout


@dataclasses.dataclass
class XenonContext:
    """
    The container which has everything for Xenon to operate
    """

    con: "console.Console"
    logger: "log.Logger"
    plugins: "plugin.XenonPluginList"
    loop: "asyncio.AbstractEventLoop"
    app: "GraiaMiraiApplication"
    bcc: "Broadcast"
    scheduler: "GraiaScheduler"


if not TYPE_CHECKING:  # real importing work
    from . import (
        command,
        config,
        console,
        database,
        dependency,
        log,
        path,
        permission,
        plugin,
        utils,
    )

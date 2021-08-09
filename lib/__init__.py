"""
The base file of Xenon library, provides `Version` class as global
"""
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # only for type checking because we don't want `Version` class to be used before its declaration in __init__.py
    from . import path, log, console, config, database
    from . import dependency, plugin, utils
    from . import permission, command


@dataclasses.dataclass(repr=False, order=True, frozen=True)
class Version:
    """
    Version object implementation
    """
    major: int
    minor: int
    micro: int
    serial: int

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.micro}.{self.serial}'

    def __repr__(self):
        return f'<Version {self.__str__()}>'


@dataclasses.dataclass
class XenonContext:
    con: 'console.Console'
    logger: 'log.Logger'
    plugins: 'plugin.XenonPluginList'


if not TYPE_CHECKING:  # real importing work
    from . import path, log, console, config, database
    from . import dependency, plugin, utils
    from . import permission, command

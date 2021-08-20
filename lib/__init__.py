# coding=utf-8
"""
Xenon库的基础，提供了基础对象Version和XenonContext的实现
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
    机器与人类均可读的 版本对象 实现

    :param major(int): 主版本
    :param minor(int): 副版本
    :param micro(int): 修订版本
    :param serial(str): 内部标记
    """

    major: int = 0
    minor: int = 0
    micro: int = 0
    serial: str = "exp"

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.micro}-{self.serial}"

    def __repr__(self):
        return f"<Version {self.__str__()}>"


__version__ = Version(minor=3, micro=1)  # check before new version rollout

state = "INIT"


@dataclasses.dataclass
class XenonContext:
    """
    含有 Xenon 所有环境信息的简单容器

    :param con: Xenon控制台实例
    :param logger: Xenon日志记录器实例
    :param plugins: Xenon插件列表实例
    :param loop: 主事件循环
    :param app: GraiaMiraiApplication
    :param bcc: BroadcastControl的实例
    :param scheduler: Scheduler实例
    """

    con: "console.Console"
    logger: "log.Logger"
    plugins: "plugin.XenonPluginList"
    loop: "asyncio.AbstractEventLoop"
    app: "GraiaMiraiApplication"
    bcc: "Broadcast"
    scheduler: "GraiaScheduler"

    def __init__(
        self,
        con: "console.Console",
        logger: "log.Logger",
        plugins: "plugin.XenonPluginList",
        loop: "asyncio.AbstractEventLoop",
        app: "GraiaMiraiApplication",
        bcc: "Broadcast",
        scheduler: "GraiaScheduler",
    ):
        """
        初始化 XenonContext。
        """
        self.con = con
        self.logger = logger
        self.plugins = plugins
        self.loop = loop
        self.app = app
        self.bcc = bcc
        self.scheduler = scheduler


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

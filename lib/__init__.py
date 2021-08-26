# coding=utf-8
"""
Xenon库的基础,提供的 `state` 属性标注了 Xenon 的运行状态
"""
__version__ = "0.4.4-beta"

from . import (
    command,
    config,
    console,
    database,
    path,
    control,
    plugin,
    utils,
)

state = "INIT"


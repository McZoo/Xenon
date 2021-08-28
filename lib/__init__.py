# coding=utf-8
"""
Xenon库的基础,提供的 `state` 属性标注了 Xenon 的运行状态
"""
__version__ = "0.5.0-beta"

from . import command, config, console, control, database, path, plugin, utils

state = "INIT"

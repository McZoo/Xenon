# coding=utf-8
"""
Xenon库的基础，提供了基础对象Version和XenonContext的实现
"""
__version__ = "0.4.0"

from . import (
    command,
    config,
    console,
    database,
    path,
    permission,
    plugin,
    utils,
)

state = "INIT"

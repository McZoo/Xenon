# coding=utf-8
"""
Xenon 日志管理
"""
import logging.handlers
from functools import partial
from logging import Logger
from os.path import join
from typing import Union

from graia.application import LoggingLogger

from . import console, path


class LogManager(logging.Formatter, logging.Filter):
    """
    集成了 格式化器 和 简易过滤器 两种功能的类
    """

    def __init__(
        self,
        level: int = logging.DEBUG,
        fmt=None,
        date_fmt=None,
        style="%",
        validate=True,
    ):
        """
        :param level: 消息过滤等级，整数
        :param fmt: 参见 `logging.Formatter.__init__`
        :param date_fmt: 参见 `logging.Formatter.__init__`
        :param style: 参见 `logging.Formatter.__init__`
        :param validate: 参见 `logging.Formatter.__init__`
        """
        logging.Formatter.__init__(self, fmt, date_fmt, style, validate)
        logging.Filter.__init__(self)
        self.filter_level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.filter_level


simple_mgr = partial(
    LogManager,
    fmt="%(asctime)s-%(name)s-%(levelno)s: %(message)s",
    date_fmt="%H:%M:%S",
    level=logging.INFO,
)

verbose_mgr = partial(
    LogManager,
    fmt="[%(asctime)s][%(name)s][%(levelname)s]: %(message)s",
    date_fmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


def create_logger(
    con: console.Console,
    con_mgr: LogManager = simple_mgr(),
    file_mgr: LogManager = verbose_mgr(),
) -> Union[Logger, LoggingLogger]:
    """
    创建 Xenon Logger 作为顶级日志记录器

    :param con: `console.Console` 实例
    :param con_mgr: 用于 控制台 的管理器实例
    :param file_mgr: 用于 保存日志文件 的管理器实例

    :return: 日志记录器
    """
    logger = logging.getLogger("")
    logger.level = logging.DEBUG
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=join(path.log, "current.log"), encoding="utf-8", when="midnight"
    )
    file_handler.namer = lambda name: name + ".log"
    con_handler = logging.handlers.QueueHandler(con.log_queue)
    file_handler.setFormatter(file_mgr)
    file_handler.addFilter(file_mgr)
    con_handler.setFormatter(con_mgr)
    con_handler.addFilter(con_mgr)
    logger.addHandler(file_handler)
    logger.addHandler(con_handler)
    return logger

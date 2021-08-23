# coding=utf-8
"""
Xenon 的工具库，封装了一些有用的函数
"""
from datetime import datetime
from os.path import join
from typing import Iterable, Optional

from croniter import croniter
from graia.application import Session
from loguru import logger
from prompt_toolkit.patch_stdout import StdoutProxy
from pydantic import AnyHttpUrl

from . import config, console, path


def config_logger():
    """
    配置 loguru 的日志记录器
    """
    logger.remove(0)  # 从 loguru 的日志记录器移除默认的配置器并重新创建
    stdout_fmt = (
        "<green>{time:HH:mm:ss}</green>-<level>{level}</level>-"
        "<cyan>{name}</cyan>: <level>{message}</level>"
    )
    logger.add(StdoutProxy(raw=True), format=stdout_fmt, level="INFO")
    logger.add(
        join(path.log, "{time: YYYY-MM-DD}.log"),
        encoding="utf-8",
        level="DEBUG",
        rotation="00:00",
    )


class SessionConfig(config.XenonConfig):
    """
    用于生成 graia.application.Session 的设置类
    """

    host: AnyHttpUrl
    account: int
    authKey: str


def get_session(con: console.Console) -> Session:
    """
    自动获取有效的 Session，并自动写入设置

    :param con: Xenon 的 Console 实例
    :return: graia.application.Session 实例
    """
    flag = False
    cfg = None
    try:
        cfg = SessionConfig.get_config("session")
    except (FileNotFoundError, KeyError):
        logger.error("Unable to load session file from local")
        # read from console
        logger.warning("Please specify session data by calling")
        logger.warning("/session HOST_ADDRESS AUTHKEY ACCOUNT")
        flag = True
    while flag:
        in_str = con.input()
        in_args = in_str.split(" ")
        if in_args[0] == "/session" and len(in_args) >= 4:
            try:
                data = {
                    "host": in_args[1],
                    "authKey": " ".join(in_args[2:-1]),
                    "account": in_args[-1],
                }
                cfg = SessionConfig(**data)
            except Exception as e:
                con.output(f"{repr(e)}")
            else:
                flag = False
    return Session(**cfg.dict())


def crontab_iter(pattern: str, base: Optional[datetime] = None) -> Iterable[datetime]:
    """\
    使用类似 crontab 的方式生成计时器

    从graia.scheduler.timer改进而来

    Args:
        :param pattern: crontab 的设置, 具体请合理使用搜索引擎
        :param base: 开始时的datetime实例，默认为datetime.now()
    """
    if base is None:
        base = datetime.now()
    iterator = croniter(pattern, base)
    while True:
        yield iterator.get_next(datetime)

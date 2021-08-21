# coding=utf-8
"""
Xenon 的工具库，封装了一些有用的函数
"""
from datetime import datetime
from typing import Iterable, Optional

from croniter import croniter
from graia.application import Session
from pydantic import AnyHttpUrl

from . import config, console, log


class SessionConfig(config.XenonConfig):
    """
    用于生成 graia.application.Session 的设置类
    """
    host: AnyHttpUrl
    account: int
    authKey: str


def get_session(con: console.Console, logger: log.Logger) -> Session:
    """
    自动获取有效的 Session，并自动写入设置

    :param con: Xenon 的 Console 实例
    :param logger: Xenon 的 Logger 实例
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
                data = {"host": in_args[1],
                        "authKey": " ".join(in_args[2:-1]),
                        "account": in_args[-1]}
                cfg = SessionConfig(**data)
            except Exception as e:
                con.output(f"{e}: {e.args}")
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

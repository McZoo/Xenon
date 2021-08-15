from datetime import datetime
from typing import Iterable, Optional

from croniter import croniter
from graia.application import Session
from pydantic import AnyHttpUrl

from . import config, console, log


@config.config
class SessionConfig:
    host: AnyHttpUrl
    account: int = config.Entry(func=int)
    authKey: str


def get_session(con: console.Console, logger: log.Logger) -> Session:
    try:
        cfg: SessionConfig = config.parse(SessionConfig, "session")
    except (FileNotFoundError, KeyError):
        logger.error("Unable to load session file from local")
        # read from console
        logger.warning("Please specify session data by calling")
        logger.warning("/session HOST_ADDRESS AUTHKEY ACCOUNT")
        flag = True
        cfg = SessionConfig()
        while flag:
            in_str = con.input()
            in_args = in_str.split(" ")
            if in_args[0] == "/session" and len(in_args) >= 4:
                cfg.host = in_args[1]
                cfg.authKey = " ".join(in_args[2:-1])
                cfg.account = int(in_args[-1])
                return Session(host=cfg.host, authKey=cfg.authKey, account=cfg.account)
    return Session(host=cfg.host, authKey=cfg.authKey, account=cfg.account)


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

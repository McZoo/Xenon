from graia.application import Session
from pydantic import AnyHttpUrl

from . import console, config, log


@config.config
class SessionConfig:
    host: AnyHttpUrl
    account: int = config.Entry(func=int)
    authKey: str


def get_session(con: console.Console, logger: log.Logger) -> Session:
    try:
        cfg: SessionConfig = config.parse(SessionConfig, 'session')
    except (FileNotFoundError, KeyError):
        logger.error("Unable to load session file from local")
        # read from console
        logger.warning("Please specify session data by calling")
        logger.warning("/session HOST_ADDRESS AUTHKEY ACCOUNT")
        flag = True
        cfg = SessionConfig()
        while flag:
            in_str = con.get_input()
            in_args = in_str.split(' ')
            if in_args[0] == '/session' and len(in_args) >= 4:
                cfg.host = in_args[1]
                cfg.authKey = ' '.join(in_args[2:-1])
                cfg.account = int(in_args[-1])
                return Session(host=cfg.host, authKey=cfg.authKey, account=cfg.account)
            else:
                con.in_queue.put(in_str)
    return Session(host=cfg.host, authKey=cfg.authKey, account=cfg.account)

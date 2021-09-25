# coding=utf-8
import asyncio
from asyncio import CancelledError
from typing import cast

from graia.application import AbstractLogger, GraiaMiraiApplication
from graia.application.exceptions import InvaildSession
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from loguru import logger

import lib

if __name__ == "__main__":
    lib.utils.cleanup_temp()
    lib.utils.config_logger()
    logger.info(f"Xenon {lib.__version__}")
    con = lib.console.Console()
    con.start()
    lib.state = "RUN"
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    con.set_bcc(bcc)
    lib.command.initialize(bcc)
    scheduler = GraiaScheduler(loop, bcc)
    db = lib.database.Database()
    loop.run_until_complete(lib.control.Permission.open_db())
    session = lib.utils.get_session(bcc)
    app = GraiaMiraiApplication(
        broadcast=bcc, connect_info=session, logger=cast(AbstractLogger, logger)
    )
    saya = Saya(bcc)
    saya.install_behaviours(BroadcastBehaviour(bcc))
    saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
    with saya.module_context():
        plugins = lib.plugin.load_plugins(saya)
    try:
        app.launch_blocking()
    except (CancelledError, InvaildSession):
        loop.run_until_complete(db.close())
    con.stop()
    lib.utils.cleanup_temp()

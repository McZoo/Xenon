# coding=utf-8
import asyncio
from typing import cast

from graia.application import GraiaMiraiApplication, AbstractLogger
from graia.application.exceptions import InvaildSession
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from loguru import logger

import lib

if __name__ == "__main__":
    lib.utils.config_logger()
    logger.info(f"Xenon {lib.__version__}")
    con = lib.console.Console()
    con.start()
    lib.state = "RUN"
    loop = asyncio.new_event_loop()
    session = lib.utils.get_session(con)
    bcc = Broadcast(loop=loop)
    con.set_bcc(bcc)
    scheduler = GraiaScheduler(loop, bcc)
    db = lib.database.Database()
    loop.run_until_complete(lib.control.Permission.open_db())
    app = GraiaMiraiApplication(
        broadcast=bcc, connect_info=session, logger=cast(AbstractLogger, logger)
    )
    lib.command.initialize(bcc)
    saya = Saya(bcc)
    saya.install_behaviours(BroadcastBehaviour(bcc))
    saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
    with saya.module_context():
        plugins = lib.plugin.load_plugins(saya)
    try:
        app.launch_blocking()
    except (asyncio.exceptions.CancelledError, InvaildSession):
        loop.run_until_complete(db.close())
        loop.stop()
        loop.close()
        del loop, bcc, scheduler, app, plugins, db
    con.stop()

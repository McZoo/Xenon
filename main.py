# coding=utf-8
import asyncio

from graia.application import GraiaMiraiApplication
from graia.application.exceptions import InvaildSession
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler

import lib

if __name__ == "__main__":
    con = lib.console.Console()
    con.start()
    logger = lib.log.create_logger(con)
    session = lib.utils.get_session(con, logger)
    while lib.state != "STOP":  # Lazarus
        lib.state = "RUN"
        loop = asyncio.new_event_loop()
        bcc = Broadcast(loop=loop)
        scheduler = GraiaScheduler(loop, bcc)
        app = GraiaMiraiApplication(broadcast=bcc, connect_info=session)
        plugins = lib.plugin.XenonPluginList.load_plugins()
        ctx = lib.XenonContext(con, logger, plugins, loop, app, bcc, scheduler)
        con.set_ctx(ctx)
        plugins.ctx = ctx
        lib.command.initialize(ctx)
        loop.run_until_complete(lib.permission.open_perm_db())
        loop.run_until_complete(plugins.prepare())
        try:
            app.launch_blocking()
        except (asyncio.exceptions.CancelledError, InvaildSession):
            loop.run_until_complete(lib.database.close_all())
            loop.stop()
            loop.close()
            del loop, bcc, scheduler, app, plugins, ctx
    con.stop()

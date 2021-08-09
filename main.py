import asyncio

from graia.application import GraiaMiraiApplication
from graia.application.exceptions import InvaildSession
from graia.broadcast import Broadcast

import lib

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    con = lib.console.Console()
    con.start()
    logger = lib.log.create_logger(con)
    session = lib.utils.get_session(con, logger)
    app = GraiaMiraiApplication(broadcast=bcc, connect_info=session)
    plugins = lib.plugin.XenonPluginList.load_plugins()
    lib.utils.log_unloaded_plugins(logger, plugins)
    ctx = lib.XenonContext(con, logger, plugins)
    plugins.execute_main(ctx)
    try:
        app.launch_blocking()
    except (asyncio.exceptions.CancelledError, InvaildSession):
        con.stop()

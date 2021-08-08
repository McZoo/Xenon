import asyncio

from graia.application import GraiaMiraiApplication, Session
from graia.application.exceptions import InvaildSession
from graia.broadcast import Broadcast

import lib

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    con = lib.console.Console()
    con.start()
    session = Session()
    app = GraiaMiraiApplication(broadcast=bcc, connect_info=session)
    try:
        app.launch_blocking()
    except (asyncio.exceptions.CancelledError, InvaildSession):
        con.stop()

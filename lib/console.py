# coding=utf-8
import asyncio
import queue
import threading
import time
from logging import LogRecord
from typing import Optional

from graia.application.event.lifecycle import ApplicationLaunched
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

import lib
from lib import permission
from lib import XenonContext
from lib.command import CommandEvent


class Console(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="ConsoleThread")
        # NEVER set daemon to True
        # NEVER
        self.out_queue: queue.Queue[str] = queue.Queue()
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.__running: bool = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.ctx: Optional[XenonContext] = None

    def stop(self):
        self.output("Press ENTER to continue...")
        self.__running = False
        self.join()

    def input(self) -> str:
        return self.in_queue.get()

    def output(self, value: str):
        self.out_queue.put(value)

    def set_ctx(self, ctx: XenonContext):
        self.ctx = ctx

        @self.ctx.bcc.receiver(ApplicationLaunched)
        async def command_poster():
            while lib.state == "RUN":
                await asyncio.sleep(0.01)
                try:
                    in_str = self.in_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    if self.ctx.bcc:
                        self.ctx.bcc.postEvent(
                            CommandEvent("local", in_str, permission.ADMIN)
                        )

    async def _a_input(self):
        p_session = PromptSession()
        while self.__running:
            await asyncio.sleep(0.01)
            with patch_stdout():
                curr_input = await p_session.prompt_async("> ")
            self.in_queue.put(curr_input)

    async def _a_output(self):
        while self.__running or self.out_queue.qsize() or self.log_queue.qsize():
            await asyncio.sleep(0.01)
            try:
                msg = self.out_queue.get_nowait()
                print(msg)
                #  Keep an eye on PT#1453
            except queue.Empty:
                pass
            try:
                rec = self.log_queue.get_nowait()
                print(rec.msg)
            except queue.Empty:
                pass

    async def _async_run(self):
        in_tsk = self.loop.create_task(self._a_input())
        out_tsk = self.loop.create_task(self._a_output())
        await out_tsk
        await in_tsk

    def run(self):
        self.__running = True
        self.out_queue.put("Starting console......")
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self._async_run())


if __name__ == "__main__":
    con = Console()
    con.start()
    while True:
        time.sleep(1)
        con.output(time.asctime())

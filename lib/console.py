import asyncio
import queue
import threading
import time
from logging import LogRecord

from graia.application.event.lifecycle import ApplicationLaunched
from graia.broadcast import Broadcast
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

import lib
from lib import permission
from lib.command import CommandEvent


class _InThread(threading.Thread):
    def __init__(self):
        super().__init__(name="Console_InThread", daemon=True)
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.loop = None
        self.bcc = None

    async def _async_run(self):
        p_session = PromptSession()
        while lib.state != "STOP":
            with patch_stdout():
                curr_input = await p_session.prompt_async("> ")
            self.in_queue.put(curr_input)

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self._async_run())

    def set_bcc(self, bcc: Broadcast):
        self.bcc = bcc

        @self.bcc.receiver(ApplicationLaunched)
        async def command_poster():
            while lib.state == "RUN":
                await asyncio.sleep(0.01)
                try:
                    in_str = self.in_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    if self.bcc:
                        self.bcc.postEvent(CommandEvent("local", in_str, permission.ADMIN))


class _OutThread(threading.Thread):
    def __init__(self):
        super().__init__(name="Console_OutThread")
        self.out_queue: queue.Queue[str] = queue.Queue()
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()

    def run(self):
        while lib.state != "STOP" or self.out_queue.qsize() or self.log_queue.qsize():
            time.sleep(0.01)
            if self.out_queue.qsize():
                msg = self.out_queue.get()
                print(msg)
                #  Keep an eye on PT#1453
            if self.log_queue.qsize():
                rec = self.log_queue.get()
                print(rec.msg)


class Console:
    def __init__(self):
        self._out = _OutThread()
        self._in = _InThread()
        self._in.start()
        self._out.start()
        self.log_queue = self._out.log_queue

    def stop(self):
        self.output("Press ENTER to continue...")
        self._out.join()
        self._in.join()

    def input(self) -> str:
        return self._in.in_queue.get()

    def output(self, value: str):
        self._out.out_queue.put(value)

    def set_bcc(self, bcc: Broadcast):
        self._in.set_bcc(bcc)

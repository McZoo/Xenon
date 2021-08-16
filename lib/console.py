import asyncio
import queue
import threading
import time
from logging import LogRecord
from typing import Callable, Coroutine, List

from graia.application.event.lifecycle import ApplicationLaunched
from graia.broadcast import Broadcast
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import prompt

from lib import permission
from lib.command import CommandEvent


class _InThread(threading.Thread):
    def __init__(self, bcc: Broadcast):
        super().__init__(name="Console_InThread", daemon=True)
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.__input_funcs: List[Callable[[str], Coroutine]] = []
        self.__running_flag = False
        self.bcc = bcc
        self.poster_online_time = 0

        @self.bcc.receiver(ApplicationLaunched)
        async def command_poster():
            time_stamp = time.time()
            self.poster_online_time = time_stamp
            while time_stamp == self.poster_online_time:
                await asyncio.sleep(0.01)
                try:
                    in_str = self.in_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    self.bcc.postEvent(CommandEvent("local", in_str, permission.ADMIN))

    def run(self):
        self.__running_flag = True
        while self.__running_flag:
            with patch_stdout():
                curr_input = prompt("> ")
            self.in_queue.put(curr_input)

    def stop(self):
        self.poster_online_time = 0
        self.__running_flag = False


class _OutThread(threading.Thread):
    def __init__(self):
        super().__init__(name="Console_OutThread")
        self.out_queue: queue.Queue[str] = queue.Queue()
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()
        self.__running_flag = False

    def stop(self):
        self.__running_flag = False

    def run(self):
        self.__running_flag = True
        while self.__running_flag or self.out_queue.qsize() or self.log_queue.qsize():
            time.sleep(0.01)
            if self.out_queue.qsize():
                msg = self.out_queue.get()
                print(msg)
                #  Keep an eye on PT#1453
            if self.log_queue.qsize():
                rec = self.log_queue.get()
                print(rec.msg)


class Console:
    def __init__(self, bcc: Broadcast):
        self._out = _OutThread()
        self._in = _InThread(bcc)
        self._in.start()
        self._out.start()
        self.log_queue = self._out.log_queue

    def stop(self):
        self.output("Press ENTER to exit program.")
        self._out.stop()
        self._out.join()
        self._in.stop()
        self._in.join()

    def input(self) -> str:
        return self._in.in_queue.get()

    def output(self, value: str):
        self._out.out_queue.put(value)

import asyncio
import queue
import sys
import threading
from logging import LogRecord
from typing import Callable, List, Coroutine

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class Console(threading.Thread):

    def __init__(self):
        super().__init__(name='TerminalThread')
        self.__loop = asyncio.new_event_loop()
        self.__out_queue: queue.Queue[str] = queue.Queue()
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.__input_func_task: List[Callable[[str], Coroutine]] = []
        self.__input_func_await: List[Callable[[str], Coroutine]] = []
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()
        self.__running_flag = False

    async def _output(self):
        while self.__running_flag or (self.__out_queue.qsize() or self.log_queue.qsize()):
            await asyncio.sleep(0.01)
            if self.__out_queue.qsize():
                msg = self.__out_queue.get()
                print(msg, file=sys.stdout)
                # TODO: replace this with prompt_toolkit.print_formatted_text after they fixed PT#1453
            if self.log_queue.qsize():
                rec = self.log_queue.get()
                print(rec.msg, file=sys.stderr)

    async def _get_con_input(self):
        session = PromptSession()
        while self.__running_flag:
            with patch_stdout():
                curr_input = await session.prompt_async('> ')
                self.in_queue.put(curr_input)
                for func in self.__input_func_task:
                    self.__loop.create_task(func(curr_input))
                for func in self.__input_func_await:
                    await func(curr_input)

    async def _async_run(self):
        output_task = self.__loop.create_task(self._output())
        await self._get_con_input()
        await output_task

    def stop(self):
        self.__running_flag = False

    def register(self, need_await: bool = False):
        def decorator(func: Callable[[str], Coroutine]):
            if need_await:
                self.__input_func_await.append(func)
            else:
                self.__input_func_task.append(func)
        return decorator

    def get_input(self) -> str:
        return self.in_queue.get()

    def put_output(self, value: str):
        self.__out_queue.put(value)

    def run(self):
        self.__running_flag = True
        self.__loop.run_until_complete(self._async_run())


if __name__ == '__main__':
    con = Console()

    @con.register(need_await=True)
    async def stopper(command: str):
        if command == '.stop':
            con.stop()
        else:
            con.put_output(command)
    con.start()
    con.join()

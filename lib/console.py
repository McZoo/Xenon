import asyncio
import queue
import sys
import threading
from logging import LogRecord

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class Console(threading.Thread):

    def __init__(self):
        super().__init__(name='TerminalThread', daemon=True)
        self.__loop = asyncio.new_event_loop()
        self.__out_queue: queue.Queue[str] = queue.Queue()
        self.__in_queue: queue.Queue[str] = queue.Queue()
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()
        self.__running_flag = False

    async def _output(self):
        while self.__running_flag or not self.__out_queue.empty() or not self.log_queue.empty():
            await asyncio.sleep(0.01)
            if not self.__out_queue.empty():
                msg = self.__out_queue.get()
                print(msg, file=sys.stdout)
                # FIXME: replace this with prompt_toolkit.print_formatted_text after they fixed PT#1453
            if not self.log_queue.empty():
                rec = self.log_queue.get()
                print(rec.msg, file=sys.stderr)

    async def _get_con_input(self):
        session = PromptSession()
        while self.__running_flag:
            with patch_stdout():
                curr_input = await session.prompt_async('> ')
                self.__in_queue.put(curr_input)

    async def _async_run(self):
        output_task = self.__loop.create_task(self._output())
        await self._get_con_input()
        await output_task

    def stop(self):
        self.__running_flag = False

    def get_input(self) -> str:
        return self.__in_queue.get()

    def put_output(self, value: str):
        self.__out_queue.put(value)

    def run(self):
        self.__running_flag = True
        self.__loop.run_until_complete(self._async_run())


if __name__ == '__main__':
    con = Console()
    con.start()
    while True:
        in_str = con.get_input()
        for _ in range(5):
            con.put_output(in_str)
        if in_str == '.stop':
            con.stop()
            break

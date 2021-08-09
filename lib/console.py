import asyncio
import queue
import sys
import threading
from logging import LogRecord
from typing import cast

from graia.application.event import ApplicationDispatcher
from graia.broadcast import BaseEvent, BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class ConsoleInputEvent(BaseEvent):
    """
    当该事件发生时, Xenon的Console从用户获得了一条命令输入。

    ** 注意: 当监听该事件或该类事件时, 请优先考虑使用原始事件类作为类型注解, 以此获得事件类实例, 便于获取更多的信息! **

    Allowed Extra Parameters(提供的额外注解支持):
        command(name, annotation=str): 用户输入的指令
    """
    type: "ConsoleInputEvent"
    command: str

    class Dispatcher(BaseDispatcher):
        mixin = [ApplicationDispatcher]

        @staticmethod
        async def catch(interface: DispatcherInterface):
            if interface.name == "command" and interface.annotation is str:
                event = cast("ConsoleInputEvent", interface.event)
                return event.command


class Console(threading.Thread):

    def __init__(self):
        super().__init__(name='TerminalThread', daemon=True)
        self.__loop = asyncio.new_event_loop()
        self.out_queue: queue.Queue[str] = queue.Queue()
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.log_queue: queue.Queue[LogRecord] = queue.Queue()
        self.__running_flag = False

    async def _output(self):
        while self.__running_flag or not self.out_queue.empty() or not self.log_queue.empty():
            await asyncio.sleep(0.01)
            if not self.out_queue.empty():
                msg = self.out_queue.get()
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
                self.in_queue.put(curr_input)

    async def _async_run(self):
        output_task = self.__loop.create_task(self._output())
        await self._get_con_input()
        await output_task

    def stop(self):
        self.__running_flag = False

    def get_input(self) -> str:
        return self.in_queue.get()

    def put_output(self, value: str):
        self.out_queue.put(value)

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

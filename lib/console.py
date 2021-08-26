# coding=utf-8
"""
Xenon 的 控制台 实现
"""
import asyncio
import queue
import threading
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from graia.application import MessageChain
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.message.elements.internal import Plain
from graia.broadcast import Broadcast
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

import lib
from lib import control
from lib.command import CommandEvent


class Console(threading.Thread):
    """
    Xenon 的控制台线程。
    """

    __current: Optional["Console"] = None

    def __init__(self):
        threading.Thread.__init__(self, name="ConsoleThread")
        # NEVER set daemon to True
        # NEVER
        self.loop_executor = ThreadPoolExecutor(
            5, thread_name_prefix="ConsoleLoopThread"
        )
        self.out_queue: queue.Queue[str] = queue.Queue()
        self.in_queue: queue.Queue[str] = queue.Queue()
        self.__running: bool = False
        self.bcc: Optional[Broadcast] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = asyncio.new_event_loop()
        self.loop.set_default_executor(self.loop_executor)
        self.__class__.__current = self

    def __del__(self):
        self.__class__.__current = None

    async def command_poster(self):
        """
        不断尝试获取新的输入，并作为 CommandEvent 广播
        """
        while lib.state == "RUN":
            await asyncio.sleep(0.01)
            try:
                in_str = self.in_queue.get_nowait()
            except queue.Empty:
                pass
            else:
                if self.bcc:
                    self.bcc.postEvent(CommandEvent("local", in_str, control.Permission.ADMIN,
                                                    MessageChain.create([Plain(in_str)])))

    def stop(self):
        """
        停止控制台。

        会阻塞直到控制台线程停止，以防止出现问题。
        """
        self.output("Press ENTER to continue...")
        self.__running = False
        self.join()
        self.__class__.__current = None

    def input(self) -> str:
        """
        从内置的输入队列直接读取。

        注意：程序不应自行使用本函数读取控制台输入，而应该通过处理 CommandEvent 获取输入。
        """
        return self.in_queue.get()

    def output(self, value: str):
        """
        直接输出消息，正常情况下程序应该尽量通过 logger 直接记录日志，
        仅应在需要和控制台确认凭证时使用

        :param value: 输出的消息
        """
        self.out_queue.put(value)

    def set_bcc(self, bcc: Broadcast):
        """
        注册发送命令事件的函数

        :param bcc: Broadcast 的实例
        """
        self.bcc = bcc
        bcc.receiver(ApplicationLaunched)(self.command_poster)

    async def _a_input(self):
        p_session = PromptSession()
        while self.__running:
            await asyncio.sleep(0.01)
            with patch_stdout():
                curr_input = await p_session.prompt_async("> ")
            if curr_input:
                self.in_queue.put(curr_input)
                logger.info(f"Command: {curr_input}")

    async def _a_output(self):
        while self.__running or self.out_queue.qsize():
            await asyncio.sleep(0.01)
            try:
                msg = self.out_queue.get_nowait()
                print(msg)
                #  Keep an eye on PT#1453
            except queue.Empty:
                pass

    async def _async_run(self):
        in_tsk = self.loop.create_task(self._a_input())
        out_tsk = self.loop.create_task(self._a_output())
        await out_tsk
        await in_tsk

    def run(self):
        """
        控制台线程的主函数。

        本线程会自动创建一个新的事件循环，并运行I/O协程
        """
        self.__running = True
        self.out_queue.put("Starting console......")
        self.loop.run_until_complete(self._async_run())

    @classmethod
    def current(cls):
        """

        :return: 当前控制台对象，没有则为 None
        """
        return cls.__current


if __name__ == "__main__":
    con = Console()
    con.start()
    while True:
        time.sleep(1)
        con.output(time.asctime())

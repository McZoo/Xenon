# coding=utf-8
"""
Xenon 的 控制台 实现
"""
import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

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
        self.in_queue: queue.Queue[str] = queue.Queue()
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
                try:
                    self.bcc.postEvent(CommandEvent("local", in_str, control.Permission.ADMIN,
                                                    MessageChain.create([Plain(in_str)])))
                except Exception as e:
                    logger.exception(e)

    def stop(self):
        """
        停止控制台。

        会阻塞直到控制台线程停止，以防止出现问题。
        """
        logger.info("Press ENTER to continue...")
        self.join()
        self.__class__.__current = None

    def input(self) -> str:
        """
        从内置的输入队列直接读取。

        注意：程序不应自行使用本函数读取控制台输入，而应该通过处理 CommandEvent 获取输入。
        """
        return self.in_queue.get()

    def set_bcc(self, bcc: Broadcast):
        """
        注册发送命令事件的函数

        :param bcc: Broadcast 的实例
        """
        self.bcc = bcc
        bcc.receiver(ApplicationLaunched)(self.command_poster)

    async def _a_input(self):
        p_session = PromptSession()
        while lib.state == "RUN":
            await asyncio.sleep(0.01)
            with patch_stdout(raw=True):
                curr_input = await p_session.prompt_async("> ", set_exception_handler=False)
            if curr_input:
                self.in_queue.put(curr_input)
                logger.info(f"Command: {curr_input}")

    def run(self):
        """
        控制台线程的主函数。

        本线程会自动创建一个新的事件循环，并运行I/O协程
        """
        logger.info("Starting console...")
        self.loop.run_until_complete(self._a_input())

    @classmethod
    def current(cls):
        """

        :return: 当前控制台对象，没有则为 None
        """
        return cls.__current

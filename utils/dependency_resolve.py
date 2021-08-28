"""
用于检查和报告依赖缺失的工具，自动输出
"""
import asyncio
import sys

from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from loguru import logger

import lib

if __name__ == "__main__":
    logger.remove(0)
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green>-<level>{level}</level>-"
            "<cyan>{name}</cyan>: <level>{message}</level>"
        ),
        level="INFO",
    )
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    scheduler = GraiaScheduler(loop, bcc)
    db = lib.database.Database()
    lib.command.initialize(bcc)
    saya = Saya(bcc)
    saya.install_behaviours(BroadcastBehaviour(bcc))
    saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
    with saya.module_context():
        plugins = lib.plugin.load_plugins(saya)
    logger.warning(
        f"{len(plugins.unloaded)} unloaded plugins,"
        f"{len(plugins.broken)} broken plugins."
    )
    logger.warning("Starting to analyze...")
    requirements_list = []
    extra_list = []
    for info in plugins.unloaded.values():
        for entry in info.spec.dependency:
            if not entry.matched:
                if entry.pypi:
                    requirements_list.append(entry.pypi)
                else:
                    extra_list.append(entry.name)
    if requirements_list:
        logger.warning("Requirements:")
        for i in requirements_list:
            logger.info(i)
        logger.info("Specify a output path:")
        path = input()
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(requirements_list))
    if extra_list:
        logger.error("Extra dependencies:")
        for i in extra_list:
            logger.info(i)
    logger.info("Complete.")
    logger.info("Exiting...")

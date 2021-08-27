# coding=utf-8
"""
Xenon 管理
"""
import time
from collections import defaultdict
from typing import Optional, Union, NoReturn, DefaultDict, Tuple, Set

from graia.application import Friend, Member, MessageChain
from graia.application.message.elements.internal import Plain

from . import database
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from .command import CommandEvent


class Permission:
    """
    用于管理权限的类，不应被实例化
    """
    cursor: Optional[database.Cursor] = None

    ADMIN = 50
    OPERATOR = 40
    MODERATOR = 30
    FRIEND = 20
    USER = 10
    BANNED = 0
    DEFAULT = USER

    levels = {
        "admin": ADMIN,
        "operator": OPERATOR,
        "op": OPERATOR,
        "moderator": MODERATOR,
        "mod": MODERATOR,
        "friend": FRIEND,
        "user": USER,
        "banned": BANNED,
        "default": DEFAULT,
    }

    @classmethod
    async def open_db(cls) -> NoReturn:
        """
        打开 Xenon 的 权限 数据库

        因为打开数据库是异步的，所以需要作为协程函数调用
        """
        db = database.Database.current()
        cls.cursor = await db.open("permission", "(id INTEGER PRIMARY KEY," "level INTEGER)")

    @classmethod
    async def get(cls, user: Union[Friend, Member, int]) -> int:
        """
        获取用户的权限

        :param user: 用户实例或QQ号
        :return: 等级，整数
        """
        if type(user) in (Friend, Member):
            user = user.id
        user: int
        res = await (await cls.cursor.select("level", (user,), "id = ?")).fetchone()
        if res is None:
            await cls.cursor.insert((user, cls.DEFAULT))
            return cls.DEFAULT
        return res[0]

    @classmethod
    async def set(cls, user: Union[Friend, Member, int], level: int) -> None:
        """
        设置用户的权限为特定等级

        :param user: 用户实例或QQ号
        :param level: 等级，整数
        """
        if type(user) in (Friend, Member):
            user = user.id
        user: int
        await cls.cursor.insert((user, level))

    @classmethod
    def require(cls, level: int) -> Depend:
        """
        指示需要 `level` 以上等级才能触发

        :param level: 限制等级
        """
        async def perm_check(event: CommandEvent):
            if event.perm_lv < level:
                raise ExecutionStop()
        return Depend(perm_check)


class Interval:
    """
    用于冷却管理的类，不应被实例化
    """
    last_exec: DefaultDict[int, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    sent_alert: Set[int] = set()

    @classmethod
    def require(cls, suspend_time: float, max_exec: int = 1,
                override_level: int = Permission.MODERATOR):
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能

        等级在 `override_level` 以上的可以无视限制

        :param suspend_time: 冷却时间
        :param max_exec: 在再次冷却前可使用次数
        :param override_level: 可超越限制的最小等级
        """
        async def cd_check(event: CommandEvent):
            if event.perm_lv >= override_level:
                return
            current = time.time()
            last = cls.last_exec[event.user]
            if current - cls.last_exec[event.user][1] >= suspend_time:
                cls.last_exec[event.user] = (1, current)
                if event.user in cls.sent_alert:
                    cls.sent_alert.remove(event.user)
                return
            elif last[0] < max_exec:
                cls.last_exec[event.user] = (last[0] + 1, current)
                if event.user in cls.sent_alert:
                    cls.sent_alert.remove(event.user)
                return
            if event.user not in cls.sent_alert:
                await event.send_result(MessageChain.create([Plain(
                    f"冷却还有{last[1] + suspend_time - current:.2f}秒结束，之后可再执行{max_exec}次"
                )]))
                cls.sent_alert.add(event.user)
            raise ExecutionStop()

        return Depend(cd_check)

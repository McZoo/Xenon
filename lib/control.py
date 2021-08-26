# coding=utf-8
"""
Xenon 管理
"""
from typing import Optional, Union, NoReturn

from graia.application import Friend, Member

from . import database
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from .command import CommandEvent


class Permission:
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
        async def perm_check(event: CommandEvent):
            if event.perm_lv < level:
                raise ExecutionStop()
        return Depend(perm_check)


class Interval:
    pass

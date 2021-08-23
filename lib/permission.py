# coding=utf-8
"""
Xenon 权限管理
"""
from typing import Optional, Union

from aiosqlite import Cursor
from graia.application import Friend, Member

from . import database

cursor: Optional[Cursor] = None

ADMIN = 50
OPERATOR = 40

FRIEND = 20
USER = 10
BANNED = 0
DEFAULT = USER

_mapping = {
    "admin": ADMIN,
    "operator": OPERATOR,
    "friend": FRIEND,
    "user": USER,
    "banned": BANNED,
    "default": DEFAULT,
}


async def open_perm_db():
    """
    打开 Xenon 的 权限 数据库

    因为打开数据库是异步的，所以需要作为协程函数调用
    """
    global cursor
    cursor = await database.Database.current().open(
        "permission", "(id INTEGER PRIMARY KEY," "level INTEGER)"
    )


async def get_perm(user: Union[Friend, Member, int]) -> int:
    """
    获取用户的权限

    :param user: 用户实例或QQ号
    :return: 等级，整数
    """
    if type(user) in (Friend, Member):
        user = user.id
    user: int
    res = await (
        await cursor.execute("SELECT level FROM permission where id = ?", (user,))
    ).fetchone()
    if res is None:
        await cursor.execute("INSERT INTO permission VALUES (?, ?)", (user, DEFAULT))
        return DEFAULT
    return res[0]


async def set_perm(user: Union[Friend, Member, int], level: int) -> None:
    """
    设置用户的权限为特定等级

    :param user: 用户实例或QQ号
    :param level: 等级，整数
    """
    if type(user) in (Friend, Member):
        user = user.id
    user: int
    await cursor.execute(
        "INSERT INTO permission VALUES (?, ?) "
        "ON CONFLICT (id) DO UPDATE SET level = excluded.level",
        (
            user,
            level,
        ),
    )

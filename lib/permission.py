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


async def get_perm(user: Union[Friend, Member, int]) -> int:
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


async def open_perm_db():
    global cursor
    cursor = await database.open_db(
        "permission", "(" "id INTEGER PRIMARY KEY," "level INTEGER" ")"
    )

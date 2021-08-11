from typing import Union, Optional

from aiosqlite import Cursor
from graia.application import Friend, Member

from . import database, XenonContext

cursor: Optional[Cursor] = None

ADMIN = 50
OPERATOR = 40

FRIEND = 20
USER = 10
BANNED = 0
DEFAULT = USER

_mapping = {"admin": ADMIN, "operator": OPERATOR, "friend": FRIEND, "user": USER, "banned": BANNED, "default": DEFAULT}


async def get_perm(user: Union[Friend, Member, int]) -> int:
    if type(user) in (Friend, Member):
        user = user.id
    user: int
    res = await (await cursor.execute("SELECT level FROM permission where id = ?", (user,))).fetchone()
    if res is None:
        await cursor.execute("INSERT INTO permission VALUES (?, ?)", (user, DEFAULT))
        return DEFAULT
    else:
        return res[0]


async def set_perm(user: Union[Friend, Member, int], level: int) -> None:
    if type(user) in (Friend, Member):
        user = user.id
    user: int
    await cursor.execute("INSERT INTO permission VALUES (?, ?) "
                         "ON CONFLICT (id) DO UPDATE SET level = excluded.level",
                         (user, level,))


async def open_perm_db(ctx: XenonContext):
    global cursor
    cursor = await database.open_db('permission',
                                    "("
                                    "id INTEGER PRIMARY KEY,"
                                    "level INTEGER"
                                    ")")

    @ctx.con.register()
    async def update_permission(command: str):
        if command.startswith('.set-perm') and len(command.split(" ")) == 3:
            _, user, lv = command.split(" ")
            try:
                user = int(user)
                if lv.lower() in _mapping:
                    lv = _mapping[lv]
                else:
                    lv = int(lv)
            except ValueError as e:
                ctx.logger.error(f"Unable to cast type: {e.args}")
            else:
                ctx.logger.debug(f"Setting user {user}'s permission to {lv}.")
                await set_perm(user, lv)

    @ctx.con.register()
    async def query_permission(command: str):
        if command.startswith('.query-perm') and len(command.split(" ")) == 2:
            _, user = command.split(" ")
            try:
                user = int(user)
            except ValueError as e:
                ctx.logger.error(f"Unable to cast type: {e.args}")
            else:
                ctx.logger.info(f"User {user}'s permission is {await get_perm(user)}")

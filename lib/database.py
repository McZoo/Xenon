from typing import List, Optional

import aiosqlite

from . import path

db_connections: List[aiosqlite.Connection] = []
db_cursor: List[aiosqlite.Cursor] = []


async def open_db(name: str, declarations: Optional[str] = None) -> aiosqlite.Cursor:
    """
    Open a database and return its cursor directly
    :param name: the name of database
    :param declarations: the data declaration part of the database. INCLUDING PARENTHESIS
    :return:
    """
    curr_conn = await aiosqlite.connect(path.join(path.database, f"{name}.sqlite"), isolation_level=None)
    db_connections.append(curr_conn)
    cursor = await curr_conn.cursor()
    db_cursor.append(cursor)
    if declarations is not None:
        await cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} {declarations};")
        # use direct replacement because it's a DDL, SQL injection? Leave that to users :P
    return cursor


async def close_all():
    for cursor in db_cursor:
        await cursor.close()
    for conn in db_connections:
        await conn.close()

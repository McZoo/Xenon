# coding=utf-8
"""
Xenon 数据库管理
"""
from typing import List, Optional

import aiosqlite

from . import path

db_connections: List[aiosqlite.Connection] = []
db_cursor: List[aiosqlite.Cursor] = []


async def open_db(name: str, declarations: Optional[str] = None) -> aiosqlite.Cursor:
    """
    打开数据库并仅返回一个光标对象进行操纵，如果提供了 `declarations` 参数将自动创建以
    `name` 作为名称的表

    注意：打开的数据库 `isolation_level` 均为 `None` ，不需要手动执行 `commit`

    数据库连接对象和本光标对象都会在执行 `close_all` 时被自动回收

    :param name: 数据库名字
    :param declarations: 数据库表的定义字段， **包括两边的小括号**
    :return: 数据库光标
    """
    curr_conn = await aiosqlite.connect(
        path.join(path.database, f"{name}.sqlite"), isolation_level=None
    )
    db_connections.append(curr_conn)
    cursor = await curr_conn.cursor()
    db_cursor.append(cursor)
    if declarations is not None:
        await cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} {declarations};")
        # use direct replacement because it's a DDL, SQL injection? Leave that to users :P
    return cursor


async def close_all():
    """
    关闭所有连接的数据库和光标
    """
    global db_cursor, db_connections
    for cursor in db_cursor:
        await cursor.close()
    for conn in db_connections:
        await conn.close()
    db_cursor = []
    db_connections = []

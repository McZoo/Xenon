# coding=utf-8
"""
Xenon 数据库管理
"""
from typing import List, Optional

import aiosqlite

from . import path


class Database:
    """
    代表Xenon数据库连接的对象，是一个 **单例类** ，插件不应自行实例化。
    """

    __current: Optional["Database"] = None

    def __init__(self):
        self.db_conn: Optional[aiosqlite.Connection] = None
        self.db_cursor: List[aiosqlite.Cursor] = []
        Database.__current = self

    async def open(
        self, name: str, declarations: Optional[str] = None
    ) -> aiosqlite.Cursor:
        """
        打开数据库名称为 `name` 的表并仅返回一个光标对象进行操纵，如果提供了 `declarations` 参数将自动创建以
        `name` 作为名称的表

        注意：打开的数据库 `isolation_level` 均为 `None` ，不需要手动执行 `commit`

        数据库连接对象和本光标对象都会在执行 `close_all` 时被自动回收

        :param name: 表名
        :param declarations: 数据库表的定义字段， **包括两边的小括号**
        :return: 数据光标
        """
        if not self.db_conn:
            self.db_conn = await aiosqlite.connect(
                path.join(path.database, "database.sqlite"), isolation_level=None
            )
        cursor = await self.db_conn.cursor()
        self.db_cursor.append(cursor)
        if declarations is not None:
            await cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} {declarations};")
            # use direct replacement because it's a DDL, SQL injection? Leave that to users :P
        return cursor

    async def close(self):
        """
        关闭所有连接的数据库和光标
        """
        for cursor in self.db_cursor:
            await cursor.close()
        await self.db_conn.close()
        self.db_cursor = []
        self.db_conn = None
        Database.__current = None

    @classmethod
    def current(cls):
        """

        :return: 当前数据库对象，没有则为 None
        """
        return cls.__current

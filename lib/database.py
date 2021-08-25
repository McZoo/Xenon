# coding=utf-8
"""
Xenon 数据库管理
"""
from typing import List, Optional, Tuple

import aiosqlite

from . import path


class Cursor(aiosqlite.Cursor):
    """
    封装了实用方法的光标类，用于类型标注，同时通过类方法赋值传递给 `aiosqlite.Cursor` 类
    """

    table: str

    async def select(
        self,
        content: str,
        values: tuple = (),
        condition: str = "",
        order_by: str = "",
        extra: str = "",
    ) -> "Cursor":
        """
        简化 SQL 的 `SELECT` 语句

        :param values: 替换 `?` 的 元组
        :param content: 查询的字段
        :param condition: 筛选条件，代替原有在 `WHERE` 后的内容
        :param order_by: 排序条件，代替原有在 `GROUP BY` 之后的内容
        :param extra: 额外部分，如 `LIMIT 1` 等
        :return: 原光标对象
        """
        base = f"SELECT {content} FROM {self.table}"
        if condition:
            base = " ".join((base, f"WHERE {condition}"))
        if order_by:
            base = " ".join((base, f"ORDER BY {order_by}"))
        if extra:
            base = " ".join((base, f"{extra}"))
        await self.execute(base, values)
        return self

    async def insert(
        self,
        values: Tuple,
        id_tuple: Tuple[str, int] = ("id", 0),
    ):
        """
        简化 SQL 的 `INSERT` 语句，同时解决了重复 ID 的问题

        :param id_tuple: 描述唯一键 ID 的 二元组，第一项为字段，第二项描述其在 `values` 中的索引
        :param values: 插入的内容
        """
        inserter = f"INSERT INTO {self.table} VALUES ({','.join('?' * len(values))})"
        deleter = f"DELETE FROM {self.table} WHERE {id_tuple[0]} = ?"
        try:
            await self.execute(inserter, values)
        except aiosqlite.IntegrityError:
            await self.execute(deleter, (values[id_tuple[1]],))
            await self.execute(inserter, values)

    async def delete(
        self,
        values: tuple,
        condition: str = "",
        extra: str = "",
    ) -> "Cursor":
        """
        简化 SQL 的 `DELETE` 语句

        :param values: 替换 `?` 的 元组
        :param condition: 条件，代替原有在 `WHERE` 后的内容
        :param extra: 额外部分，如 `LIMIT 1` 等
        :return: 原光标对象
        """
        base = f"DELETE FROM {self.table}"
        if condition:
            base = " ".join((base, f"WHERE {condition}"))
        if extra:
            base = " ".join((base, f"{extra}"))
        await self.execute(base, values)
        return self


aiosqlite.Cursor.select = Cursor.select
aiosqlite.Cursor.insert = Cursor.insert


class Database:
    """
    代表Xenon数据库连接的对象，是一个 **单例类** ，插件不应自行实例化。
    """

    __current: Optional["Database"] = None

    def __init__(self):
        self.db_conn: Optional[aiosqlite.Connection] = None
        self.db_cursor: List[aiosqlite.Cursor] = []
        Database.__current = self

    async def open(self, name: str, declarations: Optional[str] = None) -> Cursor:
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
        cursor.table = name
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

插件开发建议
==============

CommandEvent
------------
如果你在编写命令的响应器，推荐使用 Xenon 内置的 :class:`lib.command.CommandEvent`

.. code-block:: python

    from lib.command import CommandEvent
    ...

    @channel.use(ListenerSchema(listening_events=[CommandEvent]))
    async def foo(event: CommandEvent):
        if (condition): # 触发命令的条件

            ...
            msg_chain = MessageChain.create(...) # 创建回复的消息链

            await event.send_result(msg_chain) # 会自动向命令来源发送


Database
-------------
Xenon 提供了 :class:`lib.database.Database` 对象作为数据库入口。

像 `Saya` 和 `Channel` 对象一样，你可以使用 :func:`lib.database.Database.current` 方便地获取这个对象。

之后，使用 :func:`lib.database.Database.open` 方法打开你所需要的表。

如果可能，Xenon 会自动新建表，并通过传入的字段完成表的定义。

:func:`lib.database.Cursor.select` 与 :func:`lib.database.Cursor.insert` 与 :func:`lib.database.Cursor.insert`
可以用于方便地查看，修改数据库

.. code-block:: python

    from lib.database import Database
    ...

    db = Database.current()

    @channel.use(ListenerSchema(listening_events=[CommandEvent]))
    async def foo(event: CommandEvent):
        db_cur = await db.open("foo", "(id INTEGER PRIMARY KEY, bar TEXT)")
        async with db_cur:
            await db_cur.insert((ID, CONTENT)) # 可以直接插入
            await db_cur.select("*", (CONTENT,), condition="bar = ?")


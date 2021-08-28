.. _suggestions:

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


Command
------------
命令处理是QQ Bot的核心功能之一。

使用 `Graia Application` 提供的 Literature 和 Kanata 可以轻松地匹配消息链。

同时， Xenon 通过 `headless_decorator` 提供的响应控制也可清晰地完成调用限制。

参见 :class:`lib.control.Permission` 与 :class:`lib.control.Interval` 了解更多。


.. code-block:: python

    ...

    @channel.use(ListenerSchema(listening_events=[CommandEvent],
                            inline_dispatchers=[Literature(".cmd")],
                            headless_decorators=[Permission.require(Permission.USER),
                                                 Interval.require(30.0)]))
    async def parse_cmd(event: CommandEvent):
        ...

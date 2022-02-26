from datetime import datetime
import random
from typing import List, Optional, TypedDict
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import MultimediaElement
from peewee import Model, CharField, BigIntegerField, SqliteDatabase, DateTimeField, TextField, fn
from library.path import database

cave_db = SqliteDatabase(database.joinpath("cave.sqlite"))


class CaveEntry(Model):
    name = CharField()
    content = TextField()
    time = DateTimeField(default=datetime.now)
    query_time = BigIntegerField(default=0)

    class Meta:
        database = cave_db
        db_table = "entry"


CaveEntry.create_table()


def add_cave(name: str, content: MessageChain) -> int:
    for elem in content:
        if isinstance(elem, MultimediaElement):
            elem.id = None
            elem.url = None
    entry = CaveEntry(name=name, content=content.asPersistentString())
    entry.save()
    return entry.id


def del_cave(id: int) -> bool:
    if CaveEntry.get_or_none(CaveEntry.id == id):
        CaveEntry.delete().where(CaveEntry.id == id).execute()
        return True
    return False


class CaveDict(TypedDict):
    name: str
    chain: MessageChain
    query_time: str
    create_time: str
    id: str


def random_cave() -> Optional[CaveDict]:
    if CaveEntry.select().count() == 0:
        return None
    entries: List[CaveEntry] = CaveEntry.select().order_by(fn.Random())[:5]
    entry: CaveEntry = random.choice(entries)
    entry_dict: CaveDict = CaveDict(
        name=entry.name,
        chain=MessageChain.fromPersistentString(entry.content),
        create_time=entry.time.strftime("%Y-%m-%d %H:%M:%S"),
        query_time=str(entry.query_time),
        id=str(entry.id),
    )
    CaveEntry.update(query_time=entry.query_time + 1).where(CaveEntry.id == entry.id).execute()
    return entry_dict


def get_cave(id: int) -> Optional[CaveDict]:
    entry: CaveEntry = CaveEntry.get_or_none(CaveEntry.id == id)
    if entry is None:
        return None
    entry_dict: CaveDict = CaveDict(
        name=entry.name,
        chain=MessageChain.fromPersistentString(entry.content),
        create_time=entry.time.strftime("%Y-%m-%d %H:%M:%S"),
        query_time=str(entry.query_time),
        id=str(entry.id),
    )
    return entry_dict

from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.model import Group, Member
from asyncio.exceptions import TimeoutError
from . import db

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.commander.saya import CommandSchema
from graia.saya.channel import Channel
from graia.broadcast import Broadcast
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.formatter import Formatter

channel = Channel.current()


@channel.use(CommandSchema("[回声洞|.cave|cave] [add|-a] {...content:raw}"))
async def add(content: "MessageChain", broadcast: Broadcast, sender: Member, app: Ariadne, group: Group):
    if not content:
        inc = InterruptControl(broadcast)

        await app.sendMessage(group, MessageChain([At(sender), " 请发送要存入回声洞的消息\n" "发送 “取消” 来取消操作"]))

        @Waiter.create_using_function([GroupMessage])
        async def wait_for_chain(chain: MessageChain, i_sender: Member):
            if i_sender.id == sender.id and i_sender.group.id == sender.group.id:
                await chain.download_binary()
                chain = chain.include(Plain, Image)
                if chain:
                    if chain.asDisplay() != "取消":
                        id: int = db.add_cave(sender.name, chain)
                        await app.sendMessage(group, MessageChain([f"添加成功，ID: {id}"]))
                else:
                    await app.sendMessage(group, MessageChain(["请发送图片或文本"]))
                return True

        try:
            await inc.wait(wait_for_chain, timeout=60.0)
        except TimeoutError:
            await app.sendMessage(group, MessageChain(["操作超时"]))
    else:
        await content.download_binary()
        content = content.include(Plain, Image)
        if content:
            id: int = db.add_cave(sender.name, content)
            await app.sendMessage(group, MessageChain([f"添加成功，ID: {id}"]))
        else:
            await app.sendMessage(group, MessageChain(["请发送图片或文本"]))


send_fmt = Formatter(
    "回声洞 [{id}]: {create_time}\n" "共被找到 {query_time} 次\n" "{chain}\n" "          ————{name}\n"
)


@channel.use(CommandSchema("[回声洞|.cave|cave] [del|-d] {id}"))
async def delete(id: int, app: Ariadne, group: Group):
    if db.del_cave(id):
        await app.sendMessage(group, MessageChain(["删除成功"]))
    else:
        await app.sendMessage(group, MessageChain(["没有找到这条回声洞"]))


@channel.use(CommandSchema("[回声洞|.cave|cave] [get|-g] {id}"))
async def get(id: int, app: Ariadne, group: Group):
    content = db.get_cave(id)
    if content:
        await app.sendMessage(group, MessageChain(send_fmt.format(**content)))
    else:
        await app.sendMessage(group, MessageChain([f"ID: {id} 不存在"]))


@channel.use(CommandSchema("[回声洞|.cave|cave]"))
async def random_cave(app: Ariadne, group: Group):
    content = db.random_cave()
    if content:
        await app.sendMessage(group, MessageChain(send_fmt.format(**content)))
    else:
        await app.sendMessage(group, MessageChain(["没有回声洞条目, 使用 “.cave -a” 添加一条吧！"]))

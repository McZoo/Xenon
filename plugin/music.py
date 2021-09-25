# coding=utf-8
import json

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Xml
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from lib.command import CommandEvent
from lib.control import Interval, Permission

__version__ = "1.0.0"
__plugin_name__ = "music"
__author__ = "BlueGlassBlock"
__usage__ = """
.music INFO：搜索 INFO 并发送最优匹配歌曲
.music-id ID：基于网易云音乐ID发送歌曲
"""


saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".music")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(120.0),
        ],
    )
)
async def music(event: CommandEvent):
    import aiohttp

    info = event.command.removeprefix(".music ")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://cloud-music.pl-fe.cn/cloudsearch?keywords={info}"
            ) as resp:
                search_result = json.loads(await resp.text())
            if search_result["result"]["songCount"]:
                song_data = search_result["result"]["songs"][0]
                song_id = song_data["id"]
                song_name = song_data["name"]
                singers = ",".join(i["name"] for i in song_data["ar"])
                xml_text = (
                    '<?xml version="1.0"?>'
                    '<msg serviceID="2" templateID="1" action="web" '
                    f'brief="{song_name}" sourceMsgId="0" '
                    f'url="http://y.music.163.com/m/song?id={song_id}" flag="0"'
                    ' adverSign="0" multiMsgFlag="0">'
                    '<item layout="2">'
                    f"<audio "
                    'src="http://music.163.com/song/'
                    f'media/outer/url?id={song_id}.mp3"/>'
                    f"<title>{song_name}</title>"
                    f"<summary>{singers}</summary></item></msg>"
                )
                reply = MessageChain.create([Xml(xml_text)])
                return await event.send_result(reply)
            else:
                raise ValueError("无歌曲匹配")
    except Exception as e:
        reply = MessageChain.create([Plain(f"{repr(e)}")])
    else:
        reply = MessageChain.create([Plain("错误的命令")])
    await event.send_result(reply)


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".music-id")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(120.0),
        ],
    )
)
async def music(event: CommandEvent):
    import aiohttp

    info = event.command.removeprefix(".music-id ")
    try:
        song_id = int(info)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://cloud-music.pl-fe.cn/song/detail?ids={song_id}"
            ) as resp:
                search_result = json.loads(await resp.text())
            if search_result["songs"]:
                song_data = search_result["songs"][0]
                song_id = song_data["id"]
                song_name = song_data["name"]
                singers = ",".join(i["name"] for i in song_data["ar"])
                xml_text = (
                    '<?xml version="1.0"?>'
                    '<msg serviceID="2" templateID="1" action="web" '
                    f'brief="{song_name}" sourceMsgId="0" '
                    f'url="http://y.music.163.com/m/song?id={song_id}" flag="0"'
                    ' adverSign="0" multiMsgFlag="0">'
                    '<item layout="2">'
                    f"<audio "
                    'src="http://music.163.com/song/'
                    f'media/outer/url?id={song_id}.mp3"/>'
                    f"<title>{song_name}</title>"
                    f"<summary>{singers}</summary></item></msg>"
                )
                reply = MessageChain.create([Xml(xml_text)])
            else:
                raise ValueError("无歌曲匹配")
    except Exception as e:
        reply = MessageChain.create([Plain(f"{repr(e)}")])
    await event.send_result(reply)

# coding=utf-8
import json

from graia.application import MessageChain
from graia.application.message.elements.internal import Xml, Plain

import lib
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(1, 0, 0),
    "music",
    "BlueGlassBlock",
    ".music INFO：搜索 INFO 并发送最优匹配歌曲",
    lib.dependency.DependencyEntry({"aiohttp": "aiohttp"}),
)


async def main(ctx: lib.XenonContext):
    import aiohttp

    @ctx.bcc.receiver(CommandEvent)
    async def music(event: CommandEvent):
        if event.command.startswith(".music"):
            if event.command.startswith(".music "):
                info = event.command.removeprefix(".music ")
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://cloud-music.pl-fe.cn/search?keywords={info}"
                        ) as resp:
                            search_result = json.loads(await resp.text())
                        if search_result["result"]["songCount"]:
                            song_data = search_result["result"]["songs"][0]
                            song_id = song_data["id"]
                            song_name = song_data["name"]
                            singers = ",".join(i["name"] for i in song_data["artists"])
                            xml_text = (
                                '<?xml version="1.0"?>'
                                '<msg serviceID="2" templateID="1" action="web" '
                                f'brief="{song_name}" sourceMsgId="0" '
                                f'url="http://y.music.163.com/m/song?id={song_id}" flag="0"'
                                ' adverSign="0" multiMsgFlag="0">'
                                '<item layout="2">'
                                '<audio src="http://music.163.com/song/'
                                f'media/outer/url?id={song_id}.mp3"/>'
                                f"<title>{song_name}</title>"
                                f"<summary>{singers}</summary></item></msg>"
                            )
                            reply = MessageChain.create([Xml(xml_text)])
                        else:
                            raise ValueError("无歌曲匹配")
                except Exception as e:
                    reply = MessageChain.create([Plain(f"{e}: {e.args}")])
            else:
                reply = MessageChain.create([Plain("错误的命令")])
            await event.send_result(ctx, reply)
            return

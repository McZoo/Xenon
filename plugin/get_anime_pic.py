import json
from typing import TYPE_CHECKING, Tuple, Dict, Callable, Coroutine, Any

if TYPE_CHECKING:
    import aiohttp

import lib
from lib.command import CommandEvent

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Image

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 0, 1),
    "get_anime_pic",
    "BlueGlassBlock",
    lib.dependency.DependencyEntry({"aiohttp": "aiohttp"}),
)


def main(ctx: lib.XenonContext):
    import aiohttp

    async def get_lolicon() -> Tuple[bytes, str]:
        """
        Doc : https://api.lolicon.app
        """
        async with aiohttp.request("GET",
                                   "https://api.lolicon.app/"
                                   "setu/v2?size=regular&r18=0") as response:
            json_str = await response.text()
            data = json.loads(json_str)
        if data['error']:
            raise Exception(data["error"])
        else:
            data: dict = data['data'][0]
            async with aiohttp.request("GET", data['urls']['regular']) as img_resp:
                img_data = await img_resp.read()
                pid = str(data["pid"])
                return img_data, pid

    async def get_rainchan() -> Tuple[bytes, str]:
        """
        Doc : https://api.lolicon.app/#/setu
        """
        async with aiohttp.request("GET",
                                   "https://pximg.rainchan.win/img") as response:
            img_data = await response.read()
            pid = response.url.raw_query_string.removeprefix('img_id=').removesuffix('&web=true')
            return img_data, pid

    async def get_pic_re() -> Tuple[bytes, str]:
        """
        Doc: https://api.bi/docs/animeapi/
        """
        async with aiohttp.request("GET",
                                   "https://pic.re/image?nin=male&nin=r-18") as response:
            img_data = await response.read()
            return img_data, "None"

    async def get_waifu_pics_waifu() -> Tuple[bytes, str]:
        """
        Doc: https://waifu.pics/docs
        """
        async with aiohttp.request("GET",
                                   "https://api.waifu.pics/sfw/waifu") as response:
            json_str = await response.text()
            data = json.loads(json_str)
            async with aiohttp.request("GET", data['url']) as img_resp:
                img_data = await img_resp.read()
            return img_data, "None"

    async def get_waifu_pics_neko() -> Tuple[bytes, str]:
        """
        Doc: https://waifu.pics/docs
        """
        async with aiohttp.request("GET",
                                   "https://api.waifu.pics/sfw/neko") as response:
            json_str = await response.text()
            data = json.loads(json_str)
            async with aiohttp.request("GET", data['url']) as img_resp:
                img_data = await img_resp.read()
            return img_data, "None"

    async def get_sola_acg() -> Tuple[bytes, str]:
        """
        Doc: https://www.yingciyuan.cn/
        """
        async with aiohttp.request("GET",
                                   "https://www.yingciyuan.cn/pc.php") as response:
            img_data = await response.read()
            return img_data, "None"

    _api_mapping: Dict[str, Callable[[], Coroutine[Any, Any, Tuple[bytes, str]]]] = {
        "lolicon": get_lolicon,
        "rainchan": get_rainchan,
        "pic.re": get_pic_re,
        "waifu.pics/waifu": get_waifu_pics_waifu,
        "waifu.pics/neko": get_waifu_pics_neko,
        "sola-acg": get_sola_acg,
    }

    pref_cursor = None

    @ctx.bcc.receiver(CommandEvent)
    async def get_anime_pic(event: CommandEvent):
        nonlocal pref_cursor
        if pref_cursor is None:
            pref_cursor = await lib.database.open_db('get_anime_pic', "(id INTEGER PRIMARY KEY, pref TEXT)")
        if event.user and event.command == '.get_anime_pic' and event.perm_lv >= lib.permission.FRIEND:
            res = await (await pref_cursor.execute("SELECT pref FROM get_anime_pic where id = ?",
                                                   (event.user,))).fetchone()
            if res is None:
                await pref_cursor.execute("INSERT INTO get_anime_pic VALUES (?, ?)", (event.user, "rainchan"))
                pref: str = "rainchan"
            else:
                pref: str = res[0]
            func = _api_mapping.get(pref)
            try:
                img_data, pid = await func()
            except Exception as e:
                reply = MessageChain.create([Plain(f"{e}: {e.args}")])
            else:
                reply = MessageChain.create([Plain(f"API: {pref}\n"),
                                             Plain(f"PID: {pid}\n"),
                                             Image.fromUnsafeBytes(img_data)])
            if event.group:
                await ctx.app.sendGroupMessage(event.group, reply)
            else:
                await ctx.app.sendFriendMessage(event.user, reply)

    @ctx.bcc.receiver(CommandEvent)
    async def set_anime_api_pref(event: CommandEvent):
        nonlocal pref_cursor
        if pref_cursor is None:
            pref_cursor = await lib.database.open_db('get_anime_pic', "(id INTEGER PRIMARY KEY, pref TEXT)")
        if event.user and event.command.startswith(".set_anime_api_pref") and event.perm_lv >= lib.permission.FRIEND:
            if len(event.command.split(" ")) == 2:
                _, pref = event.command.split(" ")
                if pref in _api_mapping:
                    await pref_cursor.execute("INSERT INTO get_anime_pic VALUES (?, ?) "
                                              "ON CONFLICT (id) DO UPDATE SET pref = excluded.pref",
                                              (event.user, pref,))
                    reply = MessageChain.create([Plain(f"成功设置API为{pref}")])
                else:
                    reply = MessageChain.create([Plain(f"{pref}不是可用的API！")])
                if event.group:
                    await ctx.app.sendGroupMessage(event.group, reply)
                else:
                    await ctx.app.sendFriendMessage(event.user, reply)

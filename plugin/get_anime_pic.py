import json
from typing import Any, Callable, Coroutine, Dict, Tuple

from graia.application import MessageChain
from graia.application.message.elements.internal import Image, Plain

import lib
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 1, 0),
    "get_anime_pic",
    "BlueGlassBlock",
    ".get_anime_pic：从用户配置的API获取一张图片\n"
    ".set_anime_api_pref API_PROVIDER：设置用户的API为 API_PROVIDER\n"
    "API PROVIDER的可用值为：\n"
    "{ rainchan, lolicon, pic.re, \n"
    "waifu.pics/waifu, waifu.pics/neko,\n"
    "sola-acg, dmoe.cc }",
    lib.dependency.DependencyEntry({"aiohttp": "aiohttp"}),
)


async def main(ctx: lib.XenonContext):
    import aiohttp

    async def get_lolicon() -> Tuple[bytes, str]:
        """
        Doc : https://api.lolicon.app
        """
        async with aiohttp.request(
            "GET", "https://api.lolicon.app/" "setu/v2?size=regular&r18=0"
        ) as response:
            json_str = await response.text()
            data = json.loads(json_str)
        if data["error"]:
            raise Exception(data["error"])
        else:
            data: dict = data["data"][0]
            async with aiohttp.request("GET", data["urls"]["regular"]) as img_resp:
                img_data = await img_resp.read()
                pid = str(data["pid"])
                return img_data, pid

    async def get_rainchan() -> Tuple[bytes, str]:
        """
        Doc : https://api.lolicon.app/#/setu
        """
        async with aiohttp.request("GET", "https://pximg.rainchan.win/img") as response:
            img_data = await response.read()
            pid = response.url.raw_query_string.removeprefix("img_id=").removesuffix(
                "&web=true"
            )
            return img_data, pid

    async def get_pic_re() -> Tuple[bytes, str]:
        """
        Doc: https://api.bi/docs/animeapi/
        """
        async with aiohttp.request(
            "GET", "https://pic.re/image?nin=male&nin=r-18"
        ) as response:
            img_data = await response.read()
            return img_data, "None"

    async def get_waifu_pics_waifu() -> Tuple[bytes, str]:
        """
        Doc: https://waifu.pics/docs
        """
        async with aiohttp.request(
            "GET", "https://api.waifu.pics/sfw/waifu"
        ) as response:
            json_str = await response.text()
            data = json.loads(json_str)
            async with aiohttp.request("GET", data["url"]) as img_resp:
                img_data = await img_resp.read()
            return img_data, "None"

    async def get_waifu_pics_neko() -> Tuple[bytes, str]:
        """
        Doc: https://waifu.pics/docs
        """
        async with aiohttp.request(
            "GET", "https://api.waifu.pics/sfw/neko"
        ) as response:
            json_str = await response.text()
            data = json.loads(json_str)
            async with aiohttp.request("GET", data["url"]) as img_resp:
                img_data = await img_resp.read()
            return img_data, "None"

    async def get_sola_acg() -> Tuple[bytes, str]:
        """
        Doc: https://www.yingciyuan.cn/
        """
        async with aiohttp.request(
            "GET", "https://www.yingciyuan.cn/pc.php"
        ) as response:
            img_data = await response.read()
            return img_data, "None"

    async def get_dmoe_cc() -> Tuple[bytes, str]:
        """
        Doc: https://www.dmoe.cc
        """
        async with aiohttp.request("GET", "https://www.dmoe.cc/random.php") as response:
            img_data = await response.read()
            return img_data, "None"

    _api_mapping: Dict[str, Callable[[], Coroutine[Any, Any, Tuple[bytes, str]]]] = {
        "lolicon": get_lolicon,
        "rainchan": get_rainchan,
        "pic.re": get_pic_re,
        "waifu.pics/waifu": get_waifu_pics_waifu,
        "waifu.pics/neko": get_waifu_pics_neko,
        "sola-acg": get_sola_acg,
        "dmoe.cc": get_dmoe_cc,
    }

    pref_cursor = await lib.database.open_db(
        "anime_pic_db", "(id INTEGER PRIMARY KEY, pref TEXT)"
    )

    @ctx.bcc.receiver(CommandEvent)
    async def get_anime_pic(event: CommandEvent):
        if (
            event.user
            and event.command == ".get_anime_pic"
            and event.perm_lv >= lib.permission.USER
        ):
            res = await (
                await pref_cursor.execute(
                    "SELECT pref FROM anime_pic_db where id = ?", (event.user,)
                )
            ).fetchone()
            if res is None:
                await pref_cursor.execute(
                    "INSERT INTO anime_pic_db VALUES (?, ?)", (event.user, "rainchan")
                )
                pref: str = "rainchan"
            else:
                pref: str = res[0]
            func = _api_mapping.get(pref)
            try:
                img_data, pid = await func()
            except Exception as e:
                reply = MessageChain.create([Plain(f"{e}: {e.args}")])
            else:
                reply = MessageChain.create(
                    [
                        Plain(f"API: {pref}\n"),
                        Plain(f"PID: {pid}\n"),
                        Image.fromUnsafeBytes(img_data),
                    ]
                )
            if event.group:
                await ctx.app.sendGroupMessage(event.group, reply)
            else:
                await ctx.app.sendFriendMessage(event.user, reply)

    @ctx.bcc.receiver(CommandEvent)
    async def set_anime_api_pref(event: CommandEvent):
        if (
            event.user
            and event.command.startswith(".set_anime_api_pref")
            and event.perm_lv >= lib.permission.FRIEND
        ):
            if len(event.command.split(" ")) == 2:
                _, pref = event.command.split(" ")
                if pref in _api_mapping:
                    await pref_cursor.execute(
                        "INSERT INTO anime_pic_db VALUES (?, ?) "
                        "ON CONFLICT (id) DO UPDATE SET pref = excluded.pref",
                        (
                            event.user,
                            pref,
                        ),
                    )
                    reply = MessageChain.create([Plain(f"成功设置API为{pref}")])
                else:
                    reply = MessageChain.create([Plain(f"{pref}不是可用的API！")])
                if event.group:
                    await ctx.app.sendGroupMessage(event.group, reply)
                else:
                    await ctx.app.sendFriendMessage(event.user, reply)

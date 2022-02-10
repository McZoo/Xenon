import json

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.commander import Arg
from graia.ariadne.message.commander.saya import CommandSchema
from graia.ariadne.message.element import Image
from graia.saya.channel import Channel

UUID_ADDRESS_STRING = "https://api.mojang.com/users/profiles/minecraft/{name}"


RENDER_ADDR = {
    "original": "https://crafatar.com/skins/{uuid}",
    "body": "https://crafatar.com/renders/body/{uuid}?overlay",
    "head": "https://crafatar.com/renders/head/{uuid}?overlay",
    "avatar": "https://crafatar.com/avatars/{uuid}?overlay",
}

channel = Channel.current()


@channel.use(
    CommandSchema(
        "[skin|皮肤] {name}",
        {"option": Arg("[--选项|--option|-O] {option}", str, "")},
    )
)
async def get_skin(name: str, option: str, event: MessageEvent, ariadne: Ariadne):
    try:
        async with aiohttp.ClientSession() as client:
            uuid_resp = await client.get(UUID_ADDRESS_STRING.format(name=name))
            uuid = json.loads(await uuid_resp.text())["id"]
            url = RENDER_ADDR.get(option, RENDER_ADDR["body"]).format(uuid=uuid)
            await ariadne.sendMessage(event, MessageChain.create([Image(url=url)]), quote=True)
    except Exception as e:
        await ariadne.sendMessage(event, MessageChain([f"无法获取皮肤: {e!r}"]))

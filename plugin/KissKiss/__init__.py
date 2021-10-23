import os
from io import BytesIO
from typing import List

import aiohttp
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Image, Plain
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema

from lib import path, utils

# 插件信息
__dependency__ = {"PIL": "pillow", "moviepy": "moviepy", "numpy": "numpy"}
__name__ = "KissKiss"
__description__ = "生成亲吻gif"
__author__ = "Super_Water_God"
__usage__ = ".kiss @TARGET"

from lib.command import CommandEvent
from lib.control import Interval, Permission

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".kiss")],
        headless_decorators=[
            Permission.require(Permission.USER),
            Interval.require(120.0),
        ],
    )
)
async def petpet_generator(event: CommandEvent, message: MessageChain):
    if event.source != "member":
        await event.send_result(MessageChain.create([Plain("请在群里使用")]))
        return
    if message.has(At) and message.get(At)[0].target != event.user:
        if not os.path.exists(path.join(path.plugin, "KissKiss/temp")):
            os.mkdir(path.join(path.plugin, "KissKiss/temp"))
        target = message.get(At)[0].target
        if event.user == target:
            await event.send_result(MessageChain.create([Plain("请不要自交~")]))
        else:
            pic = path.join(
                path.plugin, f"KissKiss/temp/tempKiss-{event.user}-{target}.gif"
            )
            await kiss(event.user, target)
            await event.send_result(MessageChain.create([Image.fromLocalFile(pic)]))


def kiss_make_frame(operator, target, i):
    import numpy
    from PIL import Image

    operator_x = [92, 135, 84, 80, 155, 60, 50, 98, 35, 38, 70, 84, 75]
    operator_y = [64, 40, 105, 110, 82, 96, 80, 55, 65, 100, 80, 65, 65]
    target_x = [58, 62, 42, 50, 56, 18, 28, 54, 46, 60, 35, 20, 40]
    target_y = [90, 95, 100, 100, 100, 120, 110, 100, 100, 100, 115, 120, 96]
    bg = Image.open(path.join(path.plugin, f"KissKiss/KissFrames/{i}.png"))
    gif_frame = Image.new("RGB", (200, 200), (255, 255, 255))
    gif_frame.paste(bg, (0, 0))
    gif_frame.paste(target, (target_x[i - 1], target_y[i - 1]), target)
    gif_frame.paste(operator, (operator_x[i - 1], operator_y[i - 1]), operator)
    return numpy.array(gif_frame)


async def kiss(operator_id, target_id) -> None:
    from moviepy.editor import ImageSequenceClip
    from PIL import Image, ImageDraw

    operator_url = f"http://q1.qlogo.cn/g?b=qq&nk={str(operator_id)}&s=640"
    target_url = f"http://q1.qlogo.cn/g?b=qq&nk={str(target_id)}&s=640"

    async with aiohttp.ClientSession() as session:
        async with session.get(url=operator_url) as resp:
            operator_img = await resp.read()
    async with aiohttp.ClientSession() as session:
        async with session.get(url=target_url) as resp:
            target_img = await resp.read()

    def __inner():
        operator = Image.open(BytesIO(operator_img))
        target = Image.open(BytesIO(target_img))
        gif_frames = []
        gif_frames: List[Image.Image]
        operator = operator.resize((40, 40), Image.ANTIALIAS)
        size = operator.size
        r2 = min(size[0], size[1])
        circle = Image.new("L", (r2, r2))
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r2, r2), fill=255)
        alpha = Image.new("L", (r2, r2), 255)
        alpha.paste(circle, (0, 0))
        operator.putalpha(alpha)

        target = target.resize((50, 50), Image.ANTIALIAS)
        size = target.size
        r2 = min(size[0], size[1])
        circle = Image.new("L", (r2, r2))
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r2, r2), fill=255)
        alpha = Image.new("L", (r2, r2), 255)
        alpha.paste(circle, (0, 0))
        target.putalpha(alpha)
        for i in range(1, 14):
            gif_frames.append(kiss_make_frame(operator, target, i))
        clip = ImageSequenceClip(gif_frames, fps=25)
        clip.write_gif(
            path.join(
                path.plugin, f"KissKiss/temp/tempKiss-{operator_id}-{target_id}.gif"
            )
        )
        clip.close()

    await utils.async_run(__inner)

import os
from io import BytesIO

import aiohttp
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import *
from graia.application.event.messages import Group, Member
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Image, Plain
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from lib import path, utils

# 插件信息
__dependency__ = {"PIL": "pillow", "moviepy": "moviepy", "numpy": "numpy"}
__name__ = "KissKiss"
__description__ = "生成亲吻gif"
__author__ = "Super_Water_God"
__usage__ = "在群内发送 亲@目标 即可"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def petpet_generator(
    app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member
):
    if (
        message.has(At)
        and message.asDisplay().startswith("亲")
        and message.get(At)[0].target != app.connect_info.account
    ):
        if not os.path.exists(path.join(path.plugin, "KissKiss/temp")):
            os.mkdir(path.join(path.plugin, "KissKiss/temp"))
        target = message.get(At)[0].target
        if member.id == target:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain("请不要自交~😋")]), quote=message[Source][0]
            )
        else:
            pic = path.join(
                path.plugin, f"KissKiss/temp/tempKiss-{member.id}-{target}.gif"
            )
            await utils.async_run(kiss, member.id, target)
            await app.sendGroupMessage(
                group, MessageChain.create([Image.fromLocalFile(pic)])
            )


def save_gif(gif_frames, dest, fps=10):
    from moviepy.editor import ImageSequenceClip

    clip = ImageSequenceClip(gif_frames, fps=fps)
    clip.write_gif(dest)
    clip.close()


def kiss_make_frame(operator, target, i):
    from PIL import Image
    import numpy

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


def kiss(operator_id, target_id) -> None:
    from PIL import Image
    from PIL import ImageDraw

    operator_url = f"http://q1.qlogo.cn/g?b=qq&nk={str(operator_id)}&s=640"
    target_url = f"http://q1.qlogo.cn/g?b=qq&nk={str(target_id)}&s=640"
    gif_frames = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url=operator_url) as resp:
            operator_img = await resp.read()
    operator = Image.open(BytesIO(operator_img))
    async with aiohttp.ClientSession() as session:
        async with session.get(url=target_url) as resp:
            target_img = await resp.read()
    target = Image.open(BytesIO(target_img))

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
    save_gif(
        gif_frames,
        path.join(path.plugin, f"KissKiss/temp/tempKiss-{operator_id}-{target_id}.gif"),
        fps=25,
    )

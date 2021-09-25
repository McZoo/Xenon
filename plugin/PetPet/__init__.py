import os
from io import BytesIO

import aiohttp
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Image
from graia.application.message.parser.literature import Literature
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema

from lib import path, utils
from lib.command import CommandEvent
from lib.control import Interval, Permission

# 插件信息
__dependency__ = {"PIL": "pillow", "moviepy": "moviepy", "numpy": "numpy"}
__name__ = "PetPet"
__description__ = "生成摸头gif"
__author__ = "SAGIRI-kawaii"
__usage__ = ".touch @TARGET"

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[CommandEvent],
        inline_dispatchers=[Literature(".touch")],
        headless_decorators=[
            Permission.require(Permission.FRIEND),
            Interval.require(120.0),
        ],
    )
)
async def petpet_generator(event: CommandEvent, message: MessageChain):
    if message.has(At):
        if not os.path.exists(path.join(path.plugin, "PetPet/temp")):
            os.mkdir(path.join(path.plugin, "PetPet/temp"))
        await petpet(message.get(At)[0].target)
        await event.send_result(
            MessageChain.create(
                [
                    Image.fromLocalFile(
                        path.join(
                            path.plugin,
                            f"PetPet/temp",
                            f"tempPetPet-{message.get(At)[0].target}.gif",
                        )
                    )
                ]
            )
        )


frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91),
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0),
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple(
    [path.join(path.plugin, f"PetPet/PetPetFrames/frame{i}.png") for i in range(5)]
)


def save_gif(gif_frames, dest, fps=10):
    """生成 gif

    将输入的帧数据合并成视频并输出为 gif

    参数
    gif_frames: list<numpy.ndarray>
    为每一帧的数据
    dest: str
    为输出路径
    fps: int, float
    为输出 gif 每秒显示的帧数

    返回
    None
    但是会输出一个符合参数的 gif
    """
    from moviepy.editor import ImageSequenceClip

    clip = ImageSequenceClip(gif_frames, fps=fps)
    clip.write_gif(dest)  # 使用 imageio
    clip.close()


# 生成函数（非数学意味）
def make_frame(avatar, i, squish=0, flip=False):
    """生成帧

    将输入的头像转变为参数指定的帧，以供 make_gif() 处理

    参数
    avatar: PIL.Image.Image
    为头像
    i: int
    为指定帧数
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    flip: bool
    为是否横向反转头像

    返回
    numpy.ndarray
    为处理完的帧的数据
    """
    import numpy
    from PIL import Image
    from PIL import ImageOps

    # 读入位置
    spec = list(frame_spec[i])
    # 将位置添加偏移量
    for j, s in enumerate(spec):
        spec[j] = int(s + squish_factor[i][j] * squish)
    # 读取手
    hand = Image.open(frames[i])
    # 反转
    if flip:
        avatar = ImageOps.mirror(avatar)
    # 将头像放缩成所需大小
    avatar = avatar.resize(
        (int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)),
        Image.ANTIALIAS,
    )
    # 并贴到空图像上
    gif_frame = Image.new("RGB", (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖（包括偏移量）
    gif_frame.paste(hand, (0, int(squish * squish_translation_factor[i])), hand)
    # 返回
    return numpy.array(gif_frame)


async def petpet(member_id, flip=False, squish=0, fps=20) -> None:
    """生成PetPet

    将输入的头像生成为所需的 PetPet 并输出

    参数
    path: str
    为头像路径
    flip: bool
    为是否横向反转头像
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    fps: int
    为输出 gif 每秒显示的帧数

    返回
    bool
    但是会输出一个符合参数的 gif
    """
    from PIL import Image

    url = f"http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640"
    gif_frames = []
    # 打开头像
    # avatar = Image.open(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            img_content = await resp.read()

    def __inner():
        avatar = Image.open(BytesIO(img_content))

        # 生成每一帧
        for i in range(5):
            gif_frames.append(make_frame(avatar, i, squish=squish, flip=flip))
        # 输出
        save_gif(
            gif_frames,
            path.join(path.plugin, f"PetPet/temp/tempPetPet-{member_id}.gif"),
            fps=fps,
        )

    await utils.async_run(__inner)

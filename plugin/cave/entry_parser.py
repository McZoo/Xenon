# coding=utf-8
import base64
import re
from typing import List

from graia.application.message.chain import MessageChain
from graia.application.message.elements import Element
from graia.application.message.elements.internal import Image, Plain

img_regex: re.Pattern = re.compile(r"<~_img_:([\w+/=]*):_img_~>")
text_regex: re.Pattern = re.compile(r"Θ∧Ξ(.*)Ξ∧Θ")


async def to_text(in_chain: MessageChain) -> str:
    out = []
    for i in in_chain:
        if isinstance(i, Plain):
            out.append(img_regex.sub(r"Θ∧Ξ\1Ξ∧Θ", i.text))
        elif isinstance(i, Image):
            try:
                data = await i.http_to_bytes()
                out.append(f"<~_img_:{base64.b64encode(data).decode()}:_img_~>")
            except ValueError:
                pass
    return "".join(out)


async def to_list(
    in_text: str, before: List[Element] = None, after: List[Element] = None
) -> MessageChain:
    pic_b64: List[str] = img_regex.findall(in_text)
    origin = img_regex.split(in_text)
    before = before if before is not None else []
    after = after if after is not None else []
    elements = before
    for val in pic_b64:
        origin[origin.index(val)] = base64.b64decode(val)
    for v in origin:
        if isinstance(v, str):
            elements.append(Plain(text_regex.sub(r"<~_img_:\1:_img_~>", v)))
        else:
            elements.append(Image.fromUnsafeBytes(v))
    elements.extend(after)
    return MessageChain.create(elements)

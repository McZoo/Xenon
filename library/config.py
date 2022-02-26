import toml
from pydantic import BaseModel

from .path import config


class XConfig(BaseModel):
    __scope__: str
    """toml 位置"""

    __dest__: str
    """配置文件名"""

    def __init__(self):
        path = config.joinpath(f"{self.__dest__}.toml")
        path.touch(exist_ok=True)
        value = toml.loads(path.read_text())
        for key in self.__scope__.split("."):
            if key:
                value = value[key]
        super().__init__(**value)

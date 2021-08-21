# coding=utf-8
"""
Xenon 的设置

基于 pydantic，为插件提供了统一的设置接口。
"""
import json
import os
from functools import partial
from typing import Optional, Literal, final

import pydantic
import yaml

from . import path


class XenonConfig(pydantic.BaseModel):
    """
    基于 BaseModel 的 设置类
    """

    name: str = ""
    _file_type: str = ""

    @classmethod
    def get_config(cls, name: str) -> Optional["XenonConfig"]:
        """
        通过 name 指定设置文件的名称

        :param name: 插件设置文件的名称

        :return: 设置 的实例
        """
        filepath_no_prefix = os.path.abspath(os.path.join(path.config, name))
        if os.path.isfile(filepath_no_prefix + ".yml"):
            filename = filepath_no_prefix + ".yml"
            f_type = "yaml"
            loader = partial(yaml.load, Loader=yaml.loader.FullLoader)
        elif os.path.isfile(filepath_no_prefix + ".json"):
            filename = filepath_no_prefix + ".json"
            f_type = "json"
            loader = partial(json.load)
        else:
            raise FileNotFoundError("Couldn't find a proper config file")
        filename: str
        with open(filename, "r", encoding="utf-8") as file:
            content = loader(file) | {"name": name, "_file_type": f_type}
            return cls(**content)

    def write(self, file_type: Literal["yaml", "json"] = "") -> None:
        """
        将当前设置写入文件，由 `self.name` 指定名称

        :param file_type: 指定文件格式，若未指定则尝试使用设置内缓存的文件类型，默认为yaml

        :return 无
        """
        filepath_no_prefix = os.path.abspath(os.path.join(path.config, self.name))
        file_type = file_type or self._file_type
        if not file_type:
            file_type = "yaml"
        if file_type == "yaml":
            filename = filepath_no_prefix + ".yml"
            dumper = partial(yaml.dump, Dumper=yaml.dumper.BaseDumper)
        elif file_type == "json":
            filename = filepath_no_prefix + ".json"
            dumper = partial(json.dump)
        else:
            raise FileNotFoundError("Couldn't find a proper config file")
        filename: str
        with open(filename, "w", encoding="utf-8") as file:
            dumper(self.dict(), file)


@final
class EmptyConfig(XenonConfig):
    """
    作为”空“设置的模板类，意味着你不应该继承它

    重载了 `get_config` 方法与 `write` 方法以避免生成空设置文件
    """

    @classmethod
    def get_config(cls, name: str) -> None:
        return None

    def write(self, file_type: Literal["yaml", "json"] = "") -> None:
        return None

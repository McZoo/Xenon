# coding=utf-8
"""
Xenon 的设置

基于 pydantic，为插件提供了统一的设置接口。
"""
import json
from json.decoder import JSONDecodeError
import os
from typing import Optional, List

import pydantic
from loguru import logger

from . import path


class XenonConfig(pydantic.BaseModel):
    """
    基于 BaseModel 的 设置类
    """

    name: str

    @classmethod
    def get_config(cls) -> Optional["XenonConfig"]:
        """
        获取设置

        :return: 设置 的实例
        """
        name = cls.__fields__["name"].default
        filename = os.path.abspath(os.path.join(path.config, name + ".json"))
        if not os.path.isfile(filename):
            with open(filename, "a", encoding="utf-8") as f:
                f.write("{}")
        with open(filename, "r", encoding="utf-8") as file:
            try:
                res = json.load(file)
            except JSONDecodeError as e:
                logger.warning(f"{repr(e)}\n Trying to resolve with default...")
                res = {}
        instance = cls(**res)
        instance.write()
        return instance

    def write(self) -> None:
        """
        将当前设置写入文件，由 `self.name` 指定名称

        :return 无
        """
        filename = os.path.abspath(os.path.join(path.config, self.name + ".json"))
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.dict(), file, indent=4)


class PathConfig(XenonConfig):
    paths: List[str]

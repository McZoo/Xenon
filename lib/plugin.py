# coding=utf-8
"""
Xenon 插件相关
"""
import importlib
import os
from importlib.util import find_spec
from types import ModuleType
from typing import Dict, List, NamedTuple, Optional

from graia.saya import Saya
from loguru import logger
from pydantic import BaseModel

from lib import path


class DependencyBroken(Exception):
    """
    指示插件的依赖已损坏，用于在插件的 `__raise__` 属性上使用
    """

    pass


class DependencyEntry(BaseModel):
    """
    描述一个依赖项
    """

    name: str
    pypi: str
    matched: bool

    def __init__(self, name: str, pypi: str):
        super().__init__(name=name, pypi=pypi, matched=bool(find_spec(name, name)))

    def __bool__(self):
        return self.matched


class PluginSpec(BaseModel):
    """
    从插件中读取信息而自动生成的插件规格实例
    """

    name: str
    doc: str
    dependency_matched: bool
    dependency: List[DependencyEntry] = []
    author: Optional[str] = None
    version: Optional[str] = None

    def __init__(self, module: ModuleType):
        data = {"dependency_matched": True}
        if hasattr(module, "__plugin_name__"):
            data["name"] = module.__plugin_name__
        else:
            data["name"] = module.__name__.split(".")[-1]  # Last part
        docs: List[str] = []
        if module.__doc__:
            docs.append(module.__doc__.strip("\n"))
        if hasattr(module, "__plugin_doc__"):
            docs.append(module.__plugin_doc__.strip("\n"))
        if hasattr(module, "__description__"):
            docs.append(module.__description__.strip("\n"))
        if hasattr(module, "__usage__"):
            docs.append("用法：")
            docs.append(module.__usage__.strip("\n"))
        data["doc"] = "\n".join(docs)
        if hasattr(module, "__version__"):
            data["version"] = module.__version__
        if hasattr(module, "__author__"):
            data["author"] = module.__author__
        if hasattr(module, "__dependency__"):
            dependency_dict: Dict[str, str] = module.__dependency__
            entry_list = []
            for t in dependency_dict.items():
                entry = DependencyEntry(*t)
                if not entry.matched:
                    data["dependency_matched"] = False
                entry_list.append(entry)
            data["dependency"] = [DependencyEntry(*t) for t in dependency_dict.items()]
            data["dependency_matched"] = all(data["dependency"])
            if hasattr(module, "__raise__"):
                if isinstance(module.__raise__, DependencyBroken):
                    data["dependency_matched"] = False
        super().__init__(**data)


class PluginInfo(NamedTuple):
    """
    描述插件的信息
    """

    name: str
    spec: PluginSpec
    plugin: ModuleType


class PluginContainer:
    """
    承载插件信息的容器
    """

    loaded: Dict[str, PluginInfo]
    unloaded: Dict[str, PluginInfo]
    broken: List[str]
    __current: Optional["PluginContainer"] = None

    def __init__(self):
        self.loaded = {}
        self.unloaded = {}
        self.broken = []
        self.__class__.__current = self

    @classmethod
    def current(cls):
        return cls.__current

    def __del__(self):
        self.__class__.__current = None


def load_plugins(saya: Saya) -> PluginContainer:
    """
    加载 `saya` 插件并自动汇总至 `PluginContainer` 对象中

    :param saya: Saya 的 实例
    :return: 插件容器
    """
    container = PluginContainer()
    for name in os.listdir(path.plugin):
        name = name.removesuffix(".py")
        if name.startswith("_") or name.endswith(".disabled"):
            continue
        import_path = f"plugin.{name}"
        try:
            saya.require(import_path)
            curr_plugin = importlib.import_module(import_path)
        except Exception as e:
            container.broken.append(name)
            logger.error(f"An error occurred when loading {name}:")
            logger.error(e)
        else:
            spec = PluginSpec(curr_plugin)
            info = PluginInfo(name, spec, curr_plugin)
            if not spec.dependency_matched:
                container.unloaded[name] = info
            else:
                container.loaded[name] = info
    return container

# coding=utf-8
"""
Xenon 插件标准相关的基类，工具类
"""
import abc
import dataclasses
import importlib
import os
from types import FunctionType, ModuleType
from typing import Dict, List, NamedTuple, Optional, Type, cast

from . import Version, XenonContext, config, dependency, path


@dataclasses.dataclass
class XenonPluginSpec:
    """
    Xenon 插件规格

    要创建一个有效的 插件规格 实例有两种途径：

    - 直接实例化本类
    - 构造任意一个具有本类中所有属性的对象
    """

    depend: dependency.DependencyEntry
    cfg_cls: Type[config.XenonConfig]
    version: Version
    name: str
    author: str
    doc_string: str
    cfg: Optional[config.XenonConfig]

    def __init__(
        self,
        version: Version,
        name: str,
        author: str,
        doc_string: str,
        depend: dependency.DependencyEntry = None,
        config_template: Type[config.XenonConfig] = config.EmptyConfig,
    ):
        self.depend = depend
        self.cfg_cls = config_template
        self.version = version
        self.author = author
        self.doc_string = doc_string
        self.name = name
        self.cfg = None

    @staticmethod
    def is_spec(obj) -> bool:
        """
        检查对象是否为有效的 插件规格

        :param obj: 对象
        :return: 布尔值，指示是否符合
        """
        if (
            hasattr(obj, "depend")
            and hasattr(obj, "cfg_cls")
            and hasattr(obj, "version")
            and hasattr(obj, "name")
            and hasattr(obj, "doc_string")
            and hasattr(obj, "author")
        ):
            # here we don't check properties' type to reduce work and speed up process
            return True
        return False


class XenonPlugin(abc.ABC):
    """
    Xenon 插件的 抽象基类
    需要具有 属性 `plugin_spec` 和 协程函数 `main`
    """

    plugin_spec: XenonPluginSpec

    @staticmethod
    def is_plugin(obj):
        """
        检查对象是否为有效的 插件

        :param obj: 对象
        :return: 布尔值，指示是否符合
        """
        if hasattr(obj, "plugin_spec") and (
            isinstance(obj.plugin_spec, XenonPluginSpec)
            or XenonPluginSpec.is_spec(obj.plugin_spec)
        ):
            if hasattr(obj, "main") and isinstance(obj.main, FunctionType):
                return True
        return False

    @abc.abstractmethod
    async def main(self, ctx: XenonContext):
        """
        每个插件都应该在执行本函数中完成所有 准备工作

        是协程函数

        :param ctx: Xenon Context
        """


class UnloadedXenonPlugin(NamedTuple):
    """
    描述一个未被成功加载的插件
    """

    plugin_module: XenonPlugin
    dependency: dependency.UnmatchedDependency
    name: str


class XenonPluginContainer:
    """
    一个存储了所有已获取插件的容器
    """

    ctx: XenonContext
    loaded: Dict[str, XenonPlugin] = {}
    unloaded: List[UnloadedXenonPlugin] = []
    broken: List[str] = []  # this is a exception because they are unable to be imported

    @classmethod
    def load_plugins(cls) -> "XenonPluginContainer":
        """
        从 `plugin` 文件夹下加载插件，会自动重载以刷新插件更改（无法保证一定最新）

        现在，插件需要是一个 “模块” （无论是包还是单个.py文件）

        注意：需要在返回的对象上执行 `prepare` 方法！

        :return: 本类的 实例，仅依据依赖项进行分流
        """
        result = cls()
        plugin_name_list = [
            i.removesuffix(".py")
            for i in os.listdir(path.plugin)
            if (
                not i.endswith(".ignore")
                and not i.endswith(".disabled")
                and not i.startswith("_")
            )
        ]  # load list of plugins
        for name in plugin_name_list:
            import_path = "".join(("plugin.", name))
            try:
                current_plugin: ModuleType = importlib.import_module(import_path)
                importlib.reload(current_plugin)
                current_plugin: XenonPlugin = cast(XenonPlugin, current_plugin)
                if not XenonPlugin.is_plugin(current_plugin):
                    raise ImportError("The module is not Xenon Plugin")
            except ImportError:
                result.broken.append(name)
            else:
                dep_check_passed, unmatched_dependency = dependency.verify_dependency(
                    current_plugin.plugin_spec.depend
                )
                if dep_check_passed:
                    result.loaded[name] = current_plugin
                else:
                    result.unloaded.append(
                        UnloadedXenonPlugin(current_plugin, unmatched_dependency, name)
                    )
        return result

    def log_unloaded_plugins(self):
        """
        向记录器发送未加载的插件，及未加载的原因
        """
        for i in self.unloaded:
            self.ctx.logger.error(
                f"Plugin {i.name} is unloaded due to following\n" "PyPI modules:"
            )
            self.ctx.logger.error("\n".join(i.dependency.pypi))
            self.ctx.logger.error("And following\n" "EXTERNAL modules:")
            self.ctx.logger.error("\n".join(i.dependency.name))

    def load_config(self):
        """
        加载插件的设置
        """
        require_remove: List[str] = []
        for name, plugin in self.loaded.items():
            try:
                spec = plugin.plugin_spec
                spec.cfg = spec.cfg_cls.get_config(spec.name)
            except Exception as e:
                self.ctx.logger.error(
                    f"Plugin {plugin.plugin_spec.name}'s config file is broken:"
                )
                self.ctx.logger.error(f"{repr(e)}")
                require_remove.append(name)
        for i in require_remove:
            broke = self.loaded.pop(i)
            self.broken.append(broke.name)

    async def execute_main(self):
        """
        批量执行插件的`main`协程函数
        """
        for plugin in self.loaded.values():
            await plugin.main(self.ctx)

    async def prepare(self):
        """
        将所有插件初始化

        在正式启动 Application 前一定要完成
        """
        self.log_unloaded_plugins()
        self.load_config()
        await self.execute_main()

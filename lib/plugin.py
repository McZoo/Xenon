# coding=utf-8
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
    Xenon's Plugin Specification
    You can either inherit a new class from XenonPluginSpec and declare the items as class variants
    or use the `__init__` method to build a new instance of XenonPluginSpec
    """

    depend: dependency.DependencyEntry
    config_template: Type[config.XenonConfigTemplate]
    version: Version
    name: str
    author: str
    doc_string: str
    cfg: Optional[config.XenonConfigTemplate]

    def __init__(
        self,
        version: Version,
        name: str,
        author: str,
        doc_string: str,
        depend: dependency.DependencyEntry = None,
        config_template: Type[config.XenonConfigTemplate] = None,
    ):
        self.depend = depend
        self.config_template = config_template
        self.version = version
        self.author = author
        self.doc_string = doc_string
        self.name = name
        self.cfg = None

    @staticmethod
    def is_spec(instance) -> bool:
        """
        Override default instance checking behavior
        :param instance: subclass / real_instance
        :return: bool
        """
        if (
            hasattr(instance, "depend")
            and hasattr(instance, "config_template")
            and hasattr(instance, "version")
            and hasattr(instance, "name")
            and hasattr(instance, "doc_string")
            and hasattr(instance, "author")
        ):
            # here we don't check properties' type to reduce work and speed up process
            return True
        return False

    def load_config(self):
        self.cfg = config.parse(self.config_template, self.name)


class XenonPlugin(abc.ABC):
    """
    Abstract base class of Xenon Plugin, in form of a python module
    For best practice, we strongly recommend you to place
    ```
    if TYPE_CHECKING:
        import modules_from_external
        import some_module
    ```
    at the top of your module for type checking purpose, and do actual importing work
    inside `load_dependency` method
    """

    plugin_spec: XenonPluginSpec

    @staticmethod
    def is_plugin(instance):
        if hasattr(instance, "plugin_spec") and (
            isinstance(instance.plugin_spec, XenonPluginSpec)
            or XenonPluginSpec.is_spec(instance.plugin_spec)
        ):
            if hasattr(instance, "main") and isinstance(instance.main, FunctionType):
                return True
        return False

    @abc.abstractmethod
    async def main(self, ctx: XenonContext):
        """
        For every plugin, it will do registration work in this plugin
        need to be a coroutine function
        :param ctx: Xenon Context
        :return: Nothing.
        """


class UnloadedXenonPlugin(NamedTuple):
    plugin_module: XenonPlugin
    dependency: dependency.UnmatchedDependency
    name: str


class XenonPluginList:
    ctx: XenonContext
    loaded: Dict[str, XenonPlugin] = {}
    unloaded: List[UnloadedXenonPlugin] = []
    broken: List[str] = []  # this is a exception because they are unable to be imported

    @classmethod
    def load_plugins(cls) -> "XenonPluginList":
        """
        Load plugins from `plugin` directory
        :return: a tuple with list containing loaded plugins, unloaded plugins, and broken plugins
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
        for i in self.unloaded:
            self.ctx.logger.error(
                f"Plugin {i.name} is unloaded due to following\n" "PyPI modules:"
            )
            self.ctx.logger.error("\n".join(i.dependency.pypi))
            self.ctx.logger.error("And following\n" "EXTERNAL modules:")
            self.ctx.logger.error("\n".join(i.dependency.name))

    def load_config(self):
        require_remove: List[str] = []
        for name, plugin in self.loaded.items():
            try:
                plugin.plugin_spec.load_config()
            except Exception as e:
                self.ctx.logger.error(
                    f"Plugin {plugin.plugin_spec.name}'s config file is broken:"
                )
                self.ctx.logger.error(f"{e}: {e.args}")
                require_remove.append(name)
        for i in require_remove:
            broke = self.loaded.pop(i)
            self.broken.append(broke.name)

    async def execute_main(self):
        for plugin in self.loaded.values():
            await plugin.main(self.ctx)

    async def prepare(self):
        self.log_unloaded_plugins()
        self.load_config()
        await self.execute_main()

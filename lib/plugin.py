import abc
import dataclasses
import importlib
import os
from types import MethodType
from typing import List, NamedTuple, cast, Type, Optional

from . import dependency, config, Version, path, XenonContext


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
    cfg: Optional[config.XenonConfigTemplate]

    def __init__(self, depend: dependency.DependencyEntry, config_template: Type[config.XenonConfigTemplate],
                 version: Version, name: str):
        self.depend = depend
        self.config_template = config_template
        self.version = version
        self.name = name
        self.cfg = None

    def __instancecheck__(self, instance) -> bool:
        """
        Override default instance checking behavior
        :param instance: subclass / real_instance
        :return: bool
        """
        if hasattr(instance, 'depend') and hasattr(instance, 'config_template') \
                and hasattr(instance, 'version') and hasattr(instance, 'name'):
            """
            here we don't check properties' type to reduce coding work
            """
            return True
        else:
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

    def __instancecheck__(self, instance):
        if hasattr(instance, 'plugin_spec') and isinstance(instance.plugin_spec, XenonPluginSpec):
            if hasattr(instance, 'load_dependency') and isinstance(instance.load_dependency, MethodType):
                if hasattr(instance, 'main') and isinstance(instance.main, MethodType):
                    return True
        return False

    @abc.abstractmethod
    def load_dependency(self):
        """
        import all the modules from external
        :return: None
        """
        pass

    @abc.abstractmethod
    def main(self, ctx: XenonContext):
        """
        For every plugin, it will do registration work in this plugin
        :param ctx: Xenon Context
        :return: Nothing.
        """
        pass


class UnloadedXenonPlugin(NamedTuple):
    plugin_module: XenonPlugin
    dependency: dependency.UnmatchedDependency
    name: str


class XenonPluginList:
    ctx: XenonContext
    loaded: List[XenonPlugin] = []
    unloaded: List[UnloadedXenonPlugin] = []
    broken: List[str] = []  # this is a exception because they are unable to be imported

    @classmethod
    def load_plugins(cls) -> 'XenonPluginList':
        """
            Load plugins from `plugin` directory
            :return: a tuple with list containing loaded plugins, unloaded plugins, and broken plugins
            """
        result = cls()
        plugin_name_list = [i.removesuffix('.py') for i in os.listdir(path.plugin) if
                            (not i.endswith('.ignore') and not i.endswith('.disabled'))]  # load list of plugins
        for name in plugin_name_list:
            import_path = ''.join(('plugin.', name))
            try:
                current_plugin: XenonPlugin = cast(importlib.import_module(import_path), XenonPlugin)
                if not isinstance(current_plugin, XenonPlugin):
                    raise ImportError('The module is not Xenon Plugin')
            except ImportError:
                result.broken.append(name)
            else:
                dep_check_passed, unmatched_dependency = dependency.verify_dependency(current_plugin.plugin_spec.depend)
                if dep_check_passed:
                    current_plugin.load_dependency()
                    result.loaded.append(current_plugin)
                else:
                    result.unloaded.append(
                        UnloadedXenonPlugin(current_plugin, unmatched_dependency, name))
        return result

    def set_ctx(self, ctx: XenonContext):
        self.ctx = ctx

    def log_unloaded_plugins(self):
        for i in self.unloaded:
            self.ctx.logger.error(f"Plugin {i.name} is unloaded due to following\n"
                                  "PyPI modules:")
            self.ctx.logger.error("\n".join(i.dependency.pypi))
            self.ctx.logger.error("And following\n"
                                  "EXTERNAL modules:")
            self.ctx.logger.error("\n".join(i.dependency.name))

    def load_config(self):
        require_remove: List[XenonPlugin] = []
        for plugin in self.loaded:
            try:
                plugin.plugin_spec.load_config()
            except Exception as e:
                self.ctx.logger.error(f"Plugin {plugin.plugin_spec.name}'s config file is abnormal:")
                self.ctx.logger.error(f"{e}: {e.args}")
                require_remove.append(plugin)
        for i in require_remove:
            self.loaded.remove(i)
            self.broken.append(i.plugin_spec.name)

    def execute_main(self):
        for plugin in self.loaded:
            plugin.main(self.ctx)

    def prepare(self):
        self.log_unloaded_plugins()
        self.load_config()
        self.execute_main()

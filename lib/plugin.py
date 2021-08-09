import abc
import dataclasses
import importlib
import os
from types import MethodType
from typing import List, NamedTuple, cast

from . import dependency, config, Version, path, XenonContext


@dataclasses.dataclass
class XenonPluginSpec:
    """
    Xenon's Plugin Specification
    You can either inherit a new class from XenonPluginSpec and declare the items as class variants
    or use the `__init__` method to build a new instance of XenonPluginSpec
    """
    depend: dependency.DependencyEntry
    config_template: config.XenonConfigTemplate
    version: Version
    name: str

    def __init__(self, depend: dependency.DependencyEntry, cfg: config.XenonConfigTemplate, version: Version,
                 name: str):
        self.depend = depend
        self.cfg = cfg
        self.version = version
        self.name = name

    def __instancecheck__(self, instance) -> bool:
        """
        Override default instance checking behavior
        :param instance: subclass / real_instance
        :return: bool
        """
        if hasattr(instance, 'depend') and hasattr(instance, 'cfg') \
                and hasattr(instance, 'version') and hasattr(instance, 'name'):
            """
            here we don't check properties' type to reduce coding work
            """
            return True
        else:
            return False


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


class XenonPluginList(NamedTuple):
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

    def execute_main(self, ctx: XenonContext):
        for plugin in self.loaded:
            plugin.main(ctx)

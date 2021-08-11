import functools
import json
import os.path
from abc import ABC, abstractmethod
from functools import partial
from types import FunctionType
from typing import Dict, Union, Type, Any, NamedTuple, List, TypeVar, Callable
import decimal

import yaml

from . import path

MISSING = object()


class Entry(NamedTuple):
    value: Any = MISSING
    func: Callable[[Any], Any] = MISSING


class ResolveEntry(NamedTuple):
    name: str
    label: Union[Type['XenonConfigTemplate'], Type]
    default: Union[Entry, Any] = MISSING
    subclass: List['ResolveEntry'] = MISSING


def resolve(cls: Type['XenonConfigTemplate']) -> List[ResolveEntry]:
    """
    Process a "XenonConfigTemplate" class recursively
    """
    if cls.resolve_result_cache__ is None:
        annotations: Dict[str, Union[type, Type['XenonConfigTemplate']]] = \
            cls.__annotations__ | {k: v for k, v in vars(cls).items() if not k.startswith('_')
                                   and not k.endswith('_') and type(v) is type}
        default = {k: v for k, v in vars(cls).items() if
                   not k.startswith('_') and not k.endswith('_') and not type(v) is type}
        subclass = {k: v.resolve_() for k, v in vars(cls).items() if not k.startswith('_')
                    and not k.endswith('_') and type(v) is type}
        result = list()
        for k, v in annotations.items():
            _default = default[k] if k in default else MISSING
            _subclass = subclass[k] if k in subclass else MISSING
            result.append(ResolveEntry(k, v, _default, _subclass))
        cls.resolve_result_cache__ = result
    return cls.resolve_result_cache__


class XenonConfigTemplate(ABC):
    __annotations__: Dict[str, Type]
    resolve_result_cache__: Union[List[ResolveEntry], None]

    @classmethod
    @abstractmethod
    def resolve_(cls) -> List[ResolveEntry]:
        pass


T_Config = TypeVar("T_Config", XenonConfigTemplate, object)


def parse_from_dict(cls: Type[T_Config], content: Dict[str, Any]):
    resolve_result: List[ResolveEntry] = cls.resolve_()
    new_instance: XenonConfigTemplate = cls()
    for entry in resolve_result:
        if entry.subclass is not MISSING:
            if entry.name in content:  # let entry.name missing situation bypass to next if statement
                setattr(new_instance, entry.name, parse_from_dict(entry.label, content[entry.name]))
        if entry.name not in content:
            if entry.default is MISSING:
                if entry.subclass is MISSING:
                    raise KeyError(f'Missing necessary key: {entry.name}')
                else:  # entry is a subclass
                    try:
                        replacement = parse_from_dict(entry.label, {})
                    except KeyError:
                        raise KeyError(f'Missing necessary key: {entry.name}')
                    else:  # this subclass could be ignored safely
                        setattr(new_instance, entry.name, replacement)
            else:
                if type(entry.default) is not Entry:
                    setattr(new_instance, entry.name, entry.default)
                else:
                    if entry.default.value is MISSING:
                        raise KeyError(f'Missing necessary key: {entry.name}')
                    else:
                        setattr(new_instance, entry.name, entry.default.value)
        else:
            if type(entry.default) is not Entry:
                setattr(new_instance, entry.name, content[entry.name])
            else:
                if isinstance(entry.default.func, FunctionType):
                    setattr(new_instance, entry.name, entry.default.func(content[entry.name]))
                else:
                    setattr(new_instance, entry.name, content[entry.name])
    return new_instance


def parse(cls: Type[T_Config], name: str) -> T_Config:
    """
    parse the Config class with a name
    :param cls: the class
    :param name: required file name
    :return: Config class's prepared instance
    :raises FileNotFoundError, KeyError
    """
    if cls is None:
        return None
    filepath_no_prefix = os.path.abspath(os.path.join(path.config, name))
    if os.path.isfile(filepath_no_prefix + '.yaml'):
        filename = filepath_no_prefix + '.yaml'
        loader = partial(yaml.load, Loader=yaml.loader.FullLoader)
    elif os.path.isfile(filepath_no_prefix + '.yml'):
        filename = filepath_no_prefix + '.yml'
        loader = partial(yaml.load, Loader=yaml.loader.FullLoader)
    elif os.path.isfile(filepath_no_prefix + '.json'):
        filename = filepath_no_prefix + '.json'
        loader = partial(json.load)
    else:
        raise FileNotFoundError("Couldn't find a proper config file")
    filename: str
    parser: Union[json, yaml]
    with open(filename, 'r', encoding="utf-8") as file:
        content = loader(file)
    return parse_from_dict(cls, content)


def config(cls: type, /):
    """
    @decorator recursively add `resolve_` method to a class to make it a `XenonConfigTemplate`
    :param cls: class
    :return: original class, casted to `XenonConfigTemplate`
    """
    cls.resolve_ = functools.partial(resolve, cls)
    cls.resolve_result_cache__ = None
    subclasses = {key: s_cls for key, s_cls in vars(cls).items() if type(s_cls) is type}
    for k, sub_cls in subclasses.items():
        setattr(cls, k, config(sub_cls))
    return cls


def bool_converter(value):
    if type(value) is str:
        value: str
        if value.lower() in ("yes", "true", "ok"):
            return True
        elif value.lower() in ("no", "false"):
            return False
        else:
            return value


def decimal_converter(value):
    if type(value) in (str, float, int):
        try:
            return decimal.Decimal(str(value))
        except decimal.InvalidOperation:
            return value
    else:
        return value

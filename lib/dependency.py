# coding=utf-8
"""
Xenon 依赖解析
"""
from importlib.util import find_spec
from typing import List, Mapping, Tuple, Union, Dict

from pydantic import BaseModel


class DependencyEntry(BaseModel):
    """
    声明外部依赖的类
    """

    names: List[str]
    pypi_list: List[Union[str, None]]
    resolvable: bool = False
    name_to_pypi: Dict[str, str]

    def __init__(self, name_to_pypi: Mapping[str, str]):
        """
        构造依赖条目

        :param name_to_pypi: 自导入路径到 PyPI 包名的映射，如果 PyPI 不存在该包则为 `None`
        """
        super().__init__(
            names=list(name_to_pypi.keys()),
            pypi_list=list(name_to_pypi.values()),
            resolvable=all(name_to_pypi.values()),
            name_to_pypi=name_to_pypi
        )


class UnmatchedDependency(BaseModel):
    """
    描述插件中未满足的需求

    属性：
        pypi (List[str]): 存在于 PyPI 上的模块包名

        name (List[str]): 不存在于 PyPI 上的模块的导入路径
    """
    pypi: List[str]
    name: List[str]


def verify_dependency(dep: DependencyEntry) -> Tuple[bool, UnmatchedDependency]:
    """
    检查一个依赖条目中是否所有项目都可用

    :param dep: 依赖条目
    :return: 二元组，第一项指示是否 完全可用，第二项为未满足的需求
    """
    result: UnmatchedDependency = UnmatchedDependency(pypi=[], name=[])
    success: bool = True
    if dep is not None:
        for name in dep.names:
            if find_spec(name) is None:
                success = False
                if (
                        pypi_name := dep.name_to_pypi.get(name) is not None
                ):  # we are able to resolve it to pypi
                    result.pypi.append(pypi_name)
                else:
                    result.name.append(name)
    return success, result

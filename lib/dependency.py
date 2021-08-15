import dataclasses
from importlib.util import find_spec
from typing import List, Mapping, NamedTuple, Tuple, Union


@dataclasses.dataclass
class DependencyEntry:
    """
    Specify external dependency requirement
    """

    names: List[str]
    pypi_list = List[Union[str, None]]
    resolvable: bool
    name_to_pypi: Mapping[str, str] = dataclasses.field(repr=False)

    def __init__(self, name_to_pypi: Mapping[str, str]):
        """
        Build dependency entry
        :param name_to_pypi: Mapping: package [import path] to its [PyPI name]
              if it's PyPI available else None
        """
        self.names = list(iter(name_to_pypi.keys()))
        self.pypi_list = list(iter(name_to_pypi.values()))
        self.resolvable = False if None in self.pypi_list else True
        self.name_to_pypi = name_to_pypi


class UnmatchedDependency(NamedTuple):
    pypi: List[str]
    name: List[str]


def verify_dependency(dep: DependencyEntry) -> Tuple[bool, UnmatchedDependency]:
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

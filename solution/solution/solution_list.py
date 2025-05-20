from enum import Enum

from .type import *

__all__ = ["SolutionList"]


class SolutionList(Enum):
    ild = "ILD", ILD

    def __init__(self, sol_name: str, sol_cls: type):
        self.__sol_name = sol_name
        self.__sol_cls = sol_cls

    @property
    def sol_name(self) -> str:
        return self.__sol_name

    @property
    def sol_cls(self) -> type:
        return self.__sol_cls

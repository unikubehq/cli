from abc import ABC, abstractmethod

from src.context.types import ContextData


class UnikubeFileVersionError(Exception):
    pass


class UnikubeFileError(Exception):
    pass


class UnikubeFile(ABC):
    def __init__(self, path: str, data: dict):
        pass

    @abstractmethod
    def get_context(self) -> ContextData:
        raise NotImplementedError

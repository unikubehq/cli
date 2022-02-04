from abc import ABC, abstractmethod

from src.context.types import ContextData


class UnikubeFileNotFoundError(Exception):
    pass


class UnikubeFileVersionError(Exception):
    pass


class UnikubeFileError(Exception):
    pass


class UnikubeFile(ABC):
    @abstractmethod
    def get_context(self) -> ContextData:
        raise NotImplementedError

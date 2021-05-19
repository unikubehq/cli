from abc import ABC, abstractmethod

from src.storage.tinydb import TinyDatabase
from src.storage.types import TinyDatabaseData


class ILocalStorage(ABC):
    @abstractmethod
    def get(self, id: str):
        raise NotImplementedError

    @abstractmethod
    def set(self, id: str, data: TinyDatabaseData):
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: str):
        raise NotImplementedError


class LocalStorage(ILocalStorage):
    table_name = "local"
    pydantic_class = TinyDatabaseData

    def __init__(self) -> None:
        # database / storage
        self.database = TinyDatabase(table_name=self.table_name)

    def get(self, id: str, **kwargs) -> TinyDatabaseData:
        try:
            document = self.database.select(id=id)
            return self.pydantic_class(**dict(document))
        except Exception:
            return self.pydantic_class(id=id, **kwargs)

    def set(self, id: str, data: TinyDatabaseData) -> None:
        self.database.update(id=id, data=data)

    def delete(self, id: str) -> None:
        self.database.delete(id=id)

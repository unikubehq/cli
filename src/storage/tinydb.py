from typing import List

from pydantic import BaseModel
from tinydb import Query, TinyDB

from src import settings
from src.storage.types import TinyDatabaseData


class TinyDatabase:
    def __init__(
        self,
        table_name="database",
    ):
        self.table_name = table_name

        self.db = TinyDB(settings.CLI_CONFIG_FILE)
        self.table = self.db.table(self.table_name)

    def select(self, id: str) -> TinyDatabaseData:
        document = self.table.get(Query().id == id)
        return document

    def insert(self, data: BaseModel) -> int:
        doc_id = self.table.insert(data.dict())
        return doc_id

    def update(self, id: str, data: BaseModel) -> List[int]:
        doc_id_list = self.table.upsert(data.dict(), Query().id == id)
        return doc_id_list

    def delete(self, id: str) -> bool:
        doc_id = self.table.remove(Query().id == id)
        if not doc_id:
            return False
        return True

    def drop(self):
        self.db.purge_table(self.table_name)

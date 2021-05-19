from src.storage.local_storage import LocalStorage
from src.storage.types import GeneralData


class LocalStorageGeneral(LocalStorage):
    table_name = GeneralData().id
    pydantic_class = GeneralData

    document_id = GeneralData().id

    def get(self) -> GeneralData:
        data = super().get(id=self.document_id)
        return self.pydantic_class(**data.dict())

    def set(self, data: GeneralData) -> None:
        super().set(id=self.document_id, data=data)

    def delete(self) -> None:
        super().delete(id=self.document_id)

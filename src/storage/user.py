from src.storage.general import LocalStorageGeneral
from src.storage.local_storage import LocalStorage
from src.storage.types import UserData


class LocalStorageUser(LocalStorage):
    table_name = "user"
    pydantic_class = UserData

    def __init__(self, user_email) -> None:
        super().__init__()

        self.user_email = user_email

    def get(self) -> UserData:
        try:
            data = super().get(id=self.user_email)
            return self.pydantic_class(**data.dict())
        except Exception:
            return UserData()

    def set(self, data: UserData) -> None:
        super().set(id=self.user_email, data=data)

    def delete(self) -> None:
        super().delete(id=self.user_email)


def get_local_storage_user():
    try:
        local_storage_general = LocalStorageGeneral()
        general_data = local_storage_general.get()
        local_storage_user = LocalStorageUser(user_email=general_data.authentication.email)
        return local_storage_user
    except Exception:
        return None

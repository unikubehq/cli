from src.local.providers.abstract_provider import AbstractK8SProviderStorage
from src.local.providers.k3d.types import K3dData
from src.storage.local_storage import LocalStorage


class K3dLocalStorage(LocalStorage):
    table_name = "k3d"
    pydantic_class = K3dData


class K3dStorage(AbstractK8SProviderStorage):
    def __init__(self, id: str) -> None:
        super().__init__(
            id=id,
            storage=K3dLocalStorage(),
        )

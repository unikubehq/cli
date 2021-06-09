from abc import ABC, abstractmethod

from src.local.providers.types import K8sProviderData
from src.local.system import Docker


class IK8sProviderStorage(ABC):
    @abstractmethod
    def get(self) -> K8sProviderData:
        raise NotImplementedError

    @abstractmethod
    def set(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError


class AbstractK8SProviderStorage(IK8sProviderStorage):
    def __init__(
        self,
        id: str,
        storage=None,
    ) -> None:
        super().__init__()

        self.id = id
        self.storage = storage

    def get(self) -> K8sProviderData:
        return self.storage.get(self.id)

    def set(self, data) -> None:
        self.storage.set(self.id, data)

    def delete(self) -> None:
        self.storage.delete(self.id)


class IK8sProvider(ABC):
    @abstractmethod
    def create(self, ingress_port: int = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError


class AbstractK8sProvider(IK8sProvider):
    provider_type = None

    def __init__(
        self,
        id: str,
        name: str = None,
        storage: AbstractK8SProviderStorage = None,
    ) -> None:
        self.id = id
        self.name = name
        self.storage = storage

    @property
    def display_name(self):
        name = self.name
        if name:
            return name

        id = self.id
        return id

    @property
    def k8s_provider_type(self):
        return self.provider_type

    def ready(self) -> bool:
        # get name
        provider_data = self.storage.get()
        name = provider_data.name
        if not name:
            return False

        return Docker().check_running(name)

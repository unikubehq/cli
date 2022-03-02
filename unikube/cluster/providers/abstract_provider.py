import socket
from abc import ABC, abstractmethod
from uuid import UUID

from semantic_version import Version


class AbstractProvider(ABC):
    provider_type = None

    def __init__(
        self,
        id: UUID,
        name: str = None,
    ) -> None:
        self.id = id
        self.name = name

    @property
    def display_name(self):
        name = self.name
        if name:
            return name

        id = self.id
        return id

    @property
    def cluster_name(self):
        cluster_name = str(self.id).replace("-", "")
        return cluster_name[:32]  # k3d: cluster name must be <= 32 characters

    @staticmethod
    def _get_random_unused_port() -> int:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(("", 0))
        _, port = tcp.getsockname()
        tcp.close()
        return port

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

    @abstractmethod
    def version(self) -> Version:
        """
        Best return a type that allows working comparisons between versions of the same provider.
        E.g. (1, 10) > (1, 2), but "1.10" < "1.2"
        """
        raise NotImplementedError

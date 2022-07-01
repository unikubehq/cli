import socket
from abc import ABC, abstractmethod
from uuid import UUID

from semantic_version import Version


class AbstractProvider(ABC):
    provider_type = None

    def __init__(
        self,
        id: UUID,
        cluster_name: str = None,
    ) -> None:
        self.id = id
        self.cluster_name = cluster_name

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
    def version(self) -> Version:
        """
        Best return a type that allows working comparisons between versions of the same provider.
        E.g. (1, 10) > (1, 2), but "1.10" < "1.2"
        """
        raise NotImplementedError

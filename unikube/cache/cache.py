import os
from typing import Optional
from uuid import UUID

from src import settings
from src.authentication.types import AuthenticationData
from src.cache.base_file_cache import BaseFileCache


class Cache(BaseFileCache):
    userId: UUID = UUID("00000000-0000-0000-0000-000000000000")
    auth: AuthenticationData = AuthenticationData()

    def __init__(self, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "cache.json", **data):
        super().__init__(file_path=file_path, file_name=file_name, **data)


class UserInfo(BaseFileCache):
    email: str
    name: Optional[str]
    familyName: Optional[str]
    givenName: Optional[str]
    avatarImage: Optional[str]

    def __init__(self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "info.json", **data):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id))
        super().__init__(id=id, file_path=file_path, file_name=file_name, **data)


class UserSettings(BaseFileCache):
    auth_host: str = settings.AUTH_DEFAULT_HOST

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "settings.json", **data
    ):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id))
        super().__init__(file_path=file_path, file_name=file_name, **data)


class UserContext(BaseFileCache):
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    deck_id: Optional[str] = None

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "context.json", **data
    ):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id), "cache")
        super().__init__(file_path=file_path, file_name=file_name, **data)

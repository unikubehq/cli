import os
from typing import Optional
from uuid import UUID

from unikube import settings
from unikube.cache.base_file_cache import BaseFileCache


class UserInfo(BaseFileCache):
    id: UUID
    email: str
    name: Optional[str]
    familyName: Optional[str]
    givenName: Optional[str]
    avatarImage: Optional[str]

    def __init__(self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "info.json", **data):
        file_path = os.path.join(file_path, "user", str(id))
        super().__init__(file_path=file_path, file_name=file_name, id=id, **data)

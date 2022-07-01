import os
from typing import Optional
from uuid import UUID

from unikube import settings
from unikube.cache.base_file_cache import BaseFileCache


class UserContext(BaseFileCache):
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    deck_id: Optional[str] = None

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "context.json", **data
    ):
        file_path = os.path.join(file_path, "user", str(id), "cache")
        super().__init__(file_path=file_path, file_name=file_name, **data)

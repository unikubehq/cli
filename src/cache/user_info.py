import json
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src import settings


class UserInfo(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    familyName: Optional[str]
    givenName: Optional[str]
    avatarImage: Optional[str]

    def __init__(self, **data):
        if not bool(data):
            data = self.load()

        if data:
            super().__init__(**data)
        else:
            super().__init__()

    def save(self):
        # create file if not exists
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(self.id))
        Path(file_path).mkdir(parents=True, exist_ok=True)

        # save user information
        file_name = os.path.join(file_path, "info.json")
        with open(file_name, "w") as f:
            json.dump(self.json(), f)

    @classmethod
    def load(cls, id: UUID) -> "UserInfo":
        file_name = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id), "info.json")
        with open(file_name, "r") as f:
            data = json.load(f.read())
        return cls(**data)

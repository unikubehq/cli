import json
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from unikube import settings


class UserContext(BaseModel):
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    deck_id: Optional[str] = None

    def __init__(self, **data):
        ID = data.get("id", None)
        if not ID:
            raise ValueError("Missing 'id'!")

        if bool(data):
            super().__init__(**data)
        else:
            self.load(ID=ID)

    def save(self):
        # create file if not exists
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(self.id), "cache")
        Path(file_path).mkdir(parents=True, exist_ok=True)

        # save user information
        file_name = os.path.join(file_path, "context.json")
        with open(file_name, "w") as f:
            json.dump(self.json(), f)

    @classmethod
    def load(cls, ID: UUID) -> "UserContext":
        file_name = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(ID), "cache", "context.json")
        with open(file_name, "r") as f:
            data = json.load(f.read())
        return cls(**data)

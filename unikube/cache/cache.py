import json
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src import settings
from src.authentication.types import AuthenticationData


class Cache(BaseModel):
    userId: UUID = UUID("00000000-0000-0000-0000-000000000000")
    auth: AuthenticationData = AuthenticationData()

    def __init__(self, **data):
        if not bool(data):
            data = self.load()

        if data:
            super().__init__(**data)
        else:
            super().__init__()

    def save(self):
        # create file if not exists
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY)
        Path(file_path).mkdir(parents=True, exist_ok=True)

        # save user information
        file_name = os.path.join(file_path, "cache.json")
        with open(file_name, "w") as f:
            json.dump(json.loads(self.json()), f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls) -> Optional[dict]:
        file_name = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "cache.json")
        try:
            with open(file_name, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return None
        except Exception:
            # TODO
            # file_to_rem = pathlib.Path("/tmp/<file_name>.txt")
            # file_to_rem.unlink()
            pass

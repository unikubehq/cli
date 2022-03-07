import json
import os
from ast import Dict
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from unikube import settings


class BaseStorage(BaseModel):
    timestamp: datetime = datetime.now()
    file_path: str
    file_name: str

    def __init__(self, file_name: str, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, data: Dict = {}, **kwargs):
        if not bool(data):
            data = self.load(file_path=file_path, file_name=file_name)

        if data:
            kwargs = {**data, **kwargs}

        super().__init__(file_path=file_path, file_name=file_name, **kwargs)

    @property
    def file_location(self):
        return os.path.join(self.file_path, self.file_name)

    def save(self):
        # create file if not exists
        Path(self.file_path).mkdir(parents=True, exist_ok=True)

        # save user information
        self.timestamp = datetime.now()
        with open(self.file_location, "w") as f:
            json.dump(json.loads(self.json(exclude={"file_path", "file_name"})), f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, file_path: str, file_name: str) -> Optional[dict]:
        file_location = os.path.join(file_path, file_name)
        try:
            with open(file_location, "r") as file:
                data = json.load(file)
            return data

        except FileNotFoundError:
            return None

        except Exception:
            file = Path(file_location)
            file.unlink()

    def delete(self):
        file = Path(self.file_location)
        file.unlink()

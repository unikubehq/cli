from pydantic import BaseModel

from src import settings


class ConfigurationData(BaseModel):
    host: str = settings.UNIKUBE_DEFAULT_HOST

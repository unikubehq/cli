from pydantic import BaseModel

from unikube.authentication.types import AuthenticationData
from unikube.context.types import ContextData
from unikube.types import ConfigurationData


class TinyDatabaseData(BaseModel):
    id: str


class GeneralData(TinyDatabaseData):
    id: str = "general"
    authentication: AuthenticationData = AuthenticationData()


class UserData(TinyDatabaseData):
    context: ContextData = ContextData()
    config: ConfigurationData = ConfigurationData()

from pydantic import BaseModel

from src.authentication.types import AuthenticationData
from src.context.types import ContextData
from src.types import ConfigurationData


class TinyDatabaseData(BaseModel):
    id: str


class GeneralData(TinyDatabaseData):
    id: str = "general"
    authentication: AuthenticationData = AuthenticationData()


class UserData(TinyDatabaseData):
    context: ContextData = ContextData()
    config: ConfigurationData = ConfigurationData()

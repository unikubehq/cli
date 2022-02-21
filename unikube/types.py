from pydantic import BaseModel


class ConfigurationData(BaseModel):
    auth_host: str = ""

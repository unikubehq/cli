from pydantic import BaseModel


class AuthenticationData(BaseModel):
    email: str = ""
    access_token: str = ""
    refresh_token: str = ""
    requesting_party_token: bool = False
    public_key: str = ""

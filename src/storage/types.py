from pydantic import BaseModel


class TinyDatabaseData(BaseModel):
    id: str

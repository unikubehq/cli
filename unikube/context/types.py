from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ContextData(BaseModel):
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    deck_id: Optional[UUID] = None

from typing import Optional

from pydantic import BaseModel


class ContextData(BaseModel):
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    package_id: Optional[str] = None

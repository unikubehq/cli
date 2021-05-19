from enum import Enum
from typing import Optional

from pydantic.main import BaseModel


class K8sProviderType(Enum):
    K3D = "k3d"


class K8sProviderData(BaseModel):
    id: str
    name: Optional[str] = None

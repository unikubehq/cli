from typing import Optional

from pydantic import BaseModel


class K3dData(BaseModel):
    api_port: str
    publisher_port: str
    kubeconfig_path: Optional[str]

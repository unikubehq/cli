from typing import Optional

from src.local.providers.types import K8sProviderData


class K3dData(K8sProviderData):
    api_port: Optional[str] = None
    publisher_port: Optional[str] = None
    kubeconfig_path: Optional[str] = None

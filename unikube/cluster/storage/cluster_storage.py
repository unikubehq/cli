import os
from typing import Dict, Optional
from uuid import UUID

from unikube import settings
from unikube.cluster.bridge.telepresence import TelepresenceData
from unikube.cluster.providers.k3d.storage import K3dData
from unikube.cluster.storage.base_storage import BaseStorage


class ClusterStorage(BaseStorage):
    id: UUID
    name: Optional[str] = None
    provider_type: str = settings.UNIKUBE_DEFAULT_PROVIDER_TYPE.name
    provider: Dict[str, K3dData] = {}
    bridge_type: str = settings.UNIKUBE_DEFAULT_BRIDGE_TYPE.name
    bridge: Dict[str, TelepresenceData] = {}

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "cluster.json", **kwargs
    ):
        file_path = os.path.join(file_path, "cluster", str(id))
        super().__init__(id=id, file_path=file_path, file_name=file_name, data=kwargs)

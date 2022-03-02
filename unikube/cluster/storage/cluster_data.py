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
    provider: Dict[str, K3dData] = {}
    bridge: Dict[str, TelepresenceData] = {}

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "cluster.json", **data
    ):
        file_path = os.path.join(file_path, "cluster", str(id))
        super().__init__(file_path=file_path, file_name=file_name, id=id, **data)

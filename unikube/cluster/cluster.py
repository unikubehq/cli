from uuid import UUID

from unikube.cli import console
from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.providers.abstract_provider import AbstractProvider
from unikube.cluster.providers.types import ProviderType
from unikube.cluster.storage.cluster_data import ClusterStorage
from unikube.cluster.system import Docker


class Cluster:
    def __init__(self, id: UUID, display_name: str = None, **kwargs):
        self.id = id
        self.__display_name = display_name

        # storage
        self.storage = ClusterStorage(id=id)

        # provider + bridge
        self.provider: AbstractProvider = None
        self.bridge: AbstractBridge = None

    @property
    def display_name(self):
        name = self.__display_name
        if name:
            return name
        return str(self.id)

    @property
    def cluster_name(self):
        cluster_name = str(self.id).replace("-", "")
        return cluster_name[:32]  # k3d: cluster name must be <= 32 characters

    @property
    def cluster_provider_type(self) -> ProviderType:
        return self.storage.provider_type

    def get_kubeconfig_path(self, provider_type: ProviderType = None):
        if not provider_type:
            provider_type = self.cluster_provider_type

        try:
            kubeconfig_path = self.storage.provider[provider_type.name].kubeconfig_path
        except Exception:
            kubeconfig_path = self.provider.kubeconfig_path

        return kubeconfig_path

    def up(self, ingress: str = None, workers: int = None):
        # pre
        if self.bridge:
            self.bridge.pre_cluster_up()

        # create/start cluster
        cluster_exists = self.provider.exists()
        if not cluster_exists:
            console.info(f"Kubernetes cluster for '{self.display_name}' does not exist, creating it now.")
            _ = self.provider.create(
                ingress_port=ingress,
                workers=workers,
            )
        else:
            console.info(f"Kubernetes cluster for '{self.display_name}' already exists, starting it now.")
            self.provider.start()

        # post
        if self.bridge:
            self.bridge.post_cluster_up()

        return True

    def down(self):
        # pre
        if self.bridge:
            self.bridge.pre_cluster_down()

        # stop cluster
        if not self.provider.exists():
            console.info(f"No Kubernetes cluster to stop for '{self.display_name}'")
            return False

        if not self.ready():
            console.info(f"Kubernetes cluster for '{self.display_name}' is not running")
            return False

        console.info(f"Stopping Kubernetes cluster for '{self.display_name}'")
        _ = self.provider.stop()

        # post
        if self.bridge:
            self.bridge.post_cluster_down()

        return True

    def delete(self):
        # pre
        if self.ready():
            console.info(f"Kubernetes cluster for '{self.display_name}' is still running")
            return False

        # delete
        console.info(f"Delete kubernetes cluster for '{self.display_name}'")
        _ = self.provider.delete()

        return True

    def ready(self) -> bool:
        return Docker().check_running(self.cluster_name)

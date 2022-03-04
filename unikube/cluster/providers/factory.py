from unikube.cluster.bridge.bridge import AbstractBridge
from unikube.cluster.bridge.telepresence import TelepresenceBuilder
from unikube.cluster.bridge.types import BridgeType
from unikube.cluster.cluster import Cluster
from unikube.cluster.providers.abstract_provider import AbstractProvider
from unikube.cluster.providers.k3d.k3d import K3dBuilder
from unikube.cluster.providers.types import ProviderType


class ClusterFactory:
    def __init__(self):
        self._builders = {}

    # provider
    def register_provider_builder(self, provider_type: ProviderType, builder):
        self._builders[provider_type.value] = builder

    def __create_provider(self, provider_type: ProviderType, **kwargs) -> AbstractProvider:
        builder = self._builders.get(provider_type.value)
        if not builder:
            raise ValueError(provider_type)
        return builder(**kwargs)

    # bridge
    def register_bridge_builder(self, bridge_type: BridgeType, builder) -> AbstractBridge:
        self._builders[bridge_type.value] = builder

    def __create_bridge(self, bridge_type: BridgeType, **kwargs):
        builder = self._builders.get(bridge_type.value)
        if not builder:
            raise ValueError(bridge_type)
        return builder(**kwargs)

    def get(self, provider_type: ProviderType, bridge_type: BridgeType = BridgeType.telepresence, **kwargs):
        cluster = Cluster(**kwargs)
        kwargs["cluster_name"] = cluster.cluster_name

        # build provider
        cluster.provider = self.__create_provider(provider_type, **kwargs)

        # build bidge
        kubeconfig_path = cluster.get_kubeconfig_path()
        cluster.bridge = self.__create_bridge(bridge_type, kubeconfig_path=kubeconfig_path)

        return cluster


kubernetes_cluster_factory = ClusterFactory()
kubernetes_cluster_factory.register_provider_builder(ProviderType.k3d, K3dBuilder())
kubernetes_cluster_factory.register_bridge_builder(BridgeType.telepresence, TelepresenceBuilder())

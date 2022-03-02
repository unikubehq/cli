from unikube.cluster.providers.k3d.k3d import K3dBuilder
from unikube.cluster.providers.types import ProviderType


class ClusterFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, provider_type: ProviderType, builder):
        self._builders[provider_type.value] = builder

    def __create(self, provider_type: ProviderType, **kwargs):
        builder = self._builders.get(provider_type.value)
        if not builder:
            raise ValueError(provider_type)
        return builder(**kwargs)

    def get(self, provider_type: ProviderType, **kwargs):
        return self.__create(provider_type, **kwargs)


kubernetes_cluster_factory = ClusterFactory()
kubernetes_cluster_factory.register_builder(ProviderType.k3d, K3dBuilder())

from typing import List, Union

import src.cli.console as console
from src import settings
from src.local.providers.abstract_provider import AbstractK8sProvider
from src.local.providers.factory import kubernetes_cluster_factory
from src.local.providers.types import K8sProviderData, K8sProviderType
from src.storage.local_storage import LocalStorage


class K8sClusterManager(LocalStorage):
    table_name = "clusters"
    pydantic_class = K8sProviderData

    def get_all(self) -> List[K8sProviderData]:
        cluster_list = []
        for item in self.database.table.all():
            try:
                cluster_data = K8sProviderData(**item)
                cluster_list.append(cluster_data)
            except Exception:
                pass

        return cluster_list

    def get_cluster_list(self, ready: bool = None):
        ls = []
        for cluster_data in self.get_all():
            for provider_type in K8sProviderType:
                if self.exists(cluster_data, provider_type):
                    # handle ready option
                    if ready:
                        kubernetes_cluster = self.select(
                            cluster_data=cluster_data,
                            cluster_provider_type=provider_type,
                        )
                        if not kubernetes_cluster:
                            continue

                        if kubernetes_cluster.ready() != ready:
                            continue

                    # append cluster to list
                    ls.append(cluster_data)

        return ls

    def exists(
        self,
        cluster_data: K8sProviderData,
        cluster_provider_type: K8sProviderType,
    ) -> bool:
        try:
            _ = self.select(
                cluster_data=cluster_data,
                cluster_provider_type=cluster_provider_type,
            )
            return True
        except Exception:
            return False

    def select(
        self,
        cluster_data: K8sProviderData,
        cluster_provider_type: K8sProviderType = settings.UNIKUBE_DEFAULT_PROVIDER_TYPE,
    ) -> Union[AbstractK8sProvider, None]:
        # create config
        config = {
            "id": cluster_data.id,
        }

        if cluster_data.name:
            config["name"] = cluster_data.name

        # get selected kubernetes cluster from factory
        try:
            kubernetes_cluster = kubernetes_cluster_factory.get(
                cluster_provider_type,
                **config,
            )
            return kubernetes_cluster
        except Exception as e:
            console.debug(e)
            return None

import os
from typing import List, Optional
from uuid import UUID

import unikube.cli.console as console
from unikube import settings
from unikube.cluster.bridge.types import BridgeType
from unikube.cluster.cluster import Cluster
from unikube.cluster.providers.factory import kubernetes_cluster_factory
from unikube.cluster.providers.types import ProviderType


class ClusterManager:
    def count_active_clusters(self) -> int:
        # TODO: determine the number of active clusters

        # for cluster_data in ctx.cluster_manager.get_all():
        #     cluster = ctx.cluster_manager.select(cluster_data=cluster_data, cluster_provider_type=cluster_provider_type)
        #     if cluster.exists() and cluster.ready():
        #         if cluster.name == project_instance["title"] and cluster.id == project_instance["id"]:
        #             console.info(f"Kubernetes cluster for '{cluster.display_name}' is already running.", _exit=True)
        #         else:
        #             console.error(
        #                 f"You cannot start multiple projects at the same time. Project {cluster.name} ({cluster.id}) is "
        #                 f"currently running. Please run 'unikube project down {cluster.id}' first and "
        #                 f"try again.",
        #                 _exit=True,
        #             )

        return 0

    def get_cluster_ids(self) -> List[UUID]:
        folder_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "cluster")
        if not os.path.isdir(folder_path):
            return []

        ids = []
        for folder_name in os.listdir(folder_path):
            try:
                cluster_id = UUID(folder_name)
                ids.append(cluster_id)
            except Exception:
                continue

        return ids

    def get_clusters(self, ready: bool = None):
        ls = []
        for cluster_id in self.get_cluster_ids():
            for provider_type in ProviderType:
                for bridge_type in BridgeType:
                    if self.exists(cluster_id, provider_type, bridge_type):
                        # handle ready option
                        cluster = self.select(
                            id=cluster_id,
                            provider_type=provider_type,
                            bridge_type=bridge_type,
                        )

                        if ready:
                            if cluster.ready() != ready:
                                continue

                        # append cluster to list
                        ls.append(cluster)
        return ls

    def exists(self, id: UUID, provider_type: ProviderType, bridge_type: BridgeType) -> bool:
        cluster = self.select(id=id, provider_type=provider_type, bridge_type=bridge_type)
        if cluster:
            return True
        return False

    def select(
        self,
        id: UUID,
        name: str = None,
        provider_type: ProviderType = settings.UNIKUBE_DEFAULT_PROVIDER_TYPE,
        bridge_type: BridgeType = settings.UNIKUBE_DEFAULT_BRIDGE_TYPE,
        exit_on_exception: bool = False,
    ) -> Optional[Cluster]:
        # create config
        config = {
            "id": id,
        }

        if name:
            config["display_name"] = name

        # get selected cluster from factory
        try:
            cluster = kubernetes_cluster_factory.get(
                provider_type,
                bridge_type,
                **config,
            )
            return cluster
        except Exception as e:
            console.debug(e)

            if exit_on_exception:
                console.error("The selected cluster does not exist.", _exit=True)

            return None

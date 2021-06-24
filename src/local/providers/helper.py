from src.cli import console
from src.local.providers.abstract_provider import AbstractK8sProvider


def get_cluster_or_exit(ctx, project_id) -> AbstractK8sProvider:
    cluster_data = ctx.cluster_manager.get(id=project_id)
    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)
    if not cluster:
        console.error("The project cluster does not exist.", _exit=True)

    return cluster

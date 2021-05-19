import click
import jwt
from click.decorators import pass_obj

from src import settings
from src.keycloak.permissions import KeycloakPermissions
from src.storage.general import LocalStorageGeneral

# from src.graphql import GraphQL


@click.command()
@pass_obj
def develop(ctx, **kwargs):
    # GraphQL
    # graph_ql = GraphQL()
    # data = graph_ql.query(
    #     """
    #     query($id: UUID)
    #         {
    #         project(id: $id) {
    #             packages {
    #                 results {
    #                     title
    #                 }
    #             }
    #         }
    #     }
    #     """,
    #     query_variables={
    #         "id": "763dce0b-487c-4eae-8c0e-c560bed2a4ca",
    #     },
    # )
    # print(data)

    # general_data = LocalStorageGeneral().get()
    # access_token = general_data.authentication.access_token
    # print(access_token)

    project_id = "5e9e3f61-83a3-4877-8693-d3422cbc6bd2"
    cluster_data = ctx.kubernetes_cluster_manager.get(id=project_id)
    print(cluster_data)
    kubernetes_cluster = ctx.kubernetes_cluster_manager.select(cluster_data=cluster_data)
    print(kubernetes_cluster.storage.get())

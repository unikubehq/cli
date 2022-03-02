import click

import unikube.cli.console as console
from unikube.cache import UserContext
from unikube.cli.context import show_context
from unikube.cluster.bridge.telepresence import Telepresence
from unikube.graphql_utils import GraphQL


@click.command()
@click.pass_obj
def ps(ctx, **kwargs):
    """
    Displays the current process state.
    """

    # cluster
    cluster_list = ctx.cluster_manager.get_clusters(ready=True)
    cluster_id_list = [cluster.id for cluster in cluster_list]

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query {
                allProjects {
                    results {
                        title
                        id
                        description
                    }
                }
            }
            """,
        )
        project_list = data["allProjects"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    cluster_data = []
    for project in project_list:
        if project["id"] in cluster_id_list:
            cluster_data.append(project)

    console.info("Project:")
    console.table(
        data={
            "id": [cluster["id"] for cluster in cluster_data],
            "title": [cluster["title"] for cluster in cluster_data],
            "description": [cluster["description"] for cluster in cluster_data],
        },
        headers=["cluster: id", "name", "description"],
    )
    console.echo("")

    # switch
    intercept_count = 0
    if cluster_data:
        cluster = ctx.cluster_manager.select(cluster_data[0]["id"], exit_on_exception=True)
        provider_data = cluster.storage.get()

        telepresence = Telepresence(provider_data)
        intercept_count = telepresence.intercept_count()

    if intercept_count == 0:
        console.info("No app switched!")
    else:
        console.info(f"Apps switched: #{intercept_count}")
    console.echo("")

    # context
    user_context = UserContext(id=ctx.user_id)
    show_context(ctx=ctx, context=user_context)

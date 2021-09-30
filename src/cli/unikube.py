import click

import src.cli.console as console
from src.graphql import GraphQL


@click.command()
@click.pass_obj
def ps(ctx, **kwargs):
    """
    Displays the current process state.
    """

    # cluster
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    cluster_id_list = [cluster.id for cluster in cluster_list]

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
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

    console.table(
        data={
            "id": [cluster["id"] for cluster in cluster_data],
            "title": [cluster["title"] for cluster in cluster_data],
            "description": [cluster["description"] for cluster in cluster_data],
        },
        headers=["cluster: id", "name", "description"],
    )

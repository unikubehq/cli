from uuid import UUID

import click

import unikube.cli.console as console
from unikube import settings
from unikube.authentication.authentication import TokenAuthentication
from unikube.cli.console.helpers import project_id_2_display_name
from unikube.cli.helper import check_ports
from unikube.cluster.bridge.types import BridgeType
from unikube.cluster.providers.types import ProviderType
from unikube.cluster.system import Docker
from unikube.graphql_utils import GraphQL


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def list(ctx, organization, **kwargs):
    """
    Display a table of all available project names alongside with the ids.
    """

    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache

    # context
    organization_id, _, _ = ctx.context.get_context_ids_from_arguments(organization_argument=organization)

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query($organization_id: UUID) {
                allProjects(organizationId: $organization_id) {
                    results {
                        title
                        id
                        description
                    }
                }
            }
            """,
            query_variables={"organization_id": organization_id},
        )
        project_list = data["allProjects"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # console
    if len(project_list) < 1:
        console.info("No projects available. Please go to https://app.unikube.io and create a project.", _exit=True)

    console.table(
        data={
            "id": [p["id"] for p in project_list],
            "title": [p["title"] for p in project_list],
            "description": [p["description"] for p in project_list],
        },
        headers=["id", "name", "description"],
    )


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def info(ctx, project=None, organization=None, **kwargs):
    """
    Displays the id, title and optional description of the selected project.
    """

    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # argument
    if not project_id:
        project_id = console.project_list(ctx, organization_id=organization_id)
        if not project_id:
            return None

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query($id: UUID!) {
                project(id: $id) {
                    id
                    title
                    description
                    specRepository
                    specRepositoryBranch
                    organization {
                        title
                    }
                }
            }
            """,
            query_variables={"id": project_id},
        )
        project_selected = data["project"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # console
    if project_selected:
        project_selected["organization"] = project_selected.pop("organization").get("title", "-")
        project_selected["repository"] = project_selected.pop("specRepository")
        project_selected["repository branch"] = project_selected.pop("specRepositoryBranch")

        console.table(
            data={
                "key": [k for k in project_selected.keys()],
                "value": [v for v in project_selected.values()],
            },
            headers=["Key", "Value"],
        )
    else:
        console.error("Project does not exist.")


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--ingress", help="Overwrite the ingress port for the project from cluster settings", default=None)
@click.option("--bridge-type", help="Specify the bridge type", default=settings.UNIKUBE_DEFAULT_BRIDGE_TYPE.name)
@click.pass_obj
def up(ctx, project: str = None, organization: str = None, ingress: str = None, bridge_type: str = None, **kwargs):
    """
    This command starts or resumes a Kubernetes cluster for the specified project. As it is a selection command, the
    project can be specified and/or filtered in several ways:

    * as a positional argument, id or project title can be specified, or from a set context
    * as an interactive selection from available projects
    * via ``-o`` or ``--organization`` option, specifying an organisation to which a project belongs

    """

    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache

    # docker deamon
    if not Docker().daemon_active():
        console.error("Docker is not running. Please start Docker before starting a project.", _exit=True)

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # bridge type
    try:
        bridge_type = BridgeType(bridge_type)
    except Exception as e:
        console.debug(e)
        console.error("Invalid bridge-type parameter.", _exit=True)

    # cluster information
    cluster_list = ctx.cluster_manager.get_clusters(ready=True)
    cluster_ids_exclude = [str(cluster.id) for cluster in cluster_list]

    # argument
    if not project_id:
        project_id = console.project_list(ctx, organization_id=organization_id, excludes=cluster_ids_exclude)
        if not project_id:
            return None

    if project_id in cluster_ids_exclude:
        console.info(f"Project '{project_id_2_display_name(ctx=ctx, id=project_id)}' is already up.", _exit=True)

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query($id: UUID) {
                project(id: $id) {
                    title
                    id
                    organization {
                        id
                    }
                    clusterSettings {
                        id
                        port
                    }
                    organization {
                        title
                    }
                }
            }
            """,
            query_variables={
                "id": str(project_id),
            },
        )
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    project_selected = data.get("project", None)
    if not project_selected:
        console.info(
            f"The project '{project_id_2_display_name(ctx=ctx, id=project_id)}' could not be found.", _exit=True
        )

    count = ctx.cluster_manager.count_active_clusters()
    if count > 0:
        # TODO: limit cluster count???
        pass

    if ingress is None:
        ingress = project_selected["clusterSettings"]["port"]

    if not_available_ports := check_ports([ingress]):
        console.error(
            "Following ports are currently busy, however needed to spin up the cluster: {}".format(
                ", ".join([str(port) for port in not_available_ports])
            ),
            _exit=True,
        )

    # cluster up
    cluster_id = UUID(project_selected["id"])
    provider_type = ProviderType.k3d
    cluster = ctx.cluster_manager.select(
        id=cluster_id, provider_type=provider_type, bridge_type=bridge_type, exit_on_exception=True
    )
    success = cluster.up()
    if not success:
        console.error("The project cluster could not be started.")

    console.success("The project cluster is up.")


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def down(ctx, project=None, organization=None, **kwargs):
    """
    Stop/pause cluster.
    """

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # cluster
    cluster_list = ctx.cluster_manager.get_clusters(ready=True)

    # argument
    if not project_id:
        project_id = console.project_list(
            ctx, organization_id=organization_id, filter=[str(cluster.id) for cluster in cluster_list]
        )
        if not project_id:
            return None

    # check if project is in local storage
    if project_id not in [cluster.id for cluster in cluster_list]:
        console.info(
            f"The project cluster for '{project_id_2_display_name(ctx=ctx, id=project_id)}' is not up or does not exist yet.",
            _exit=True,
        )

    # stop cluster
    cluster = ctx.cluster_manager.select(id=project_id, exit_on_exception=True)
    success = cluster.down()
    if not success:
        console.error("The cluster could not be stopped.")

    console.success("The project cluster is down.")


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def delete(ctx, project=None, organization=None, **kwargs):
    """
    Delete the current project and all related data.
    """

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # cluster
    cluster_list = ctx.cluster_manager.get_clusters()
    if len(cluster_list) == 0:
        console.info("No projects found.", _exit=True)

    # argument
    if not project_id:
        project_id = console.project_list(
            ctx, organization_id=organization_id, filter=[str(cluster.id) for cluster in cluster_list]
        )
        if not project_id:
            return None

    if project_id not in [cluster.id for cluster in cluster_list]:
        console.info(
            f"The project cluster for '{project_id_2_display_name(ctx=ctx, id=project_id)}' could not be found.",
            _exit=True,
        )

    # warning
    console.warning("Deleting a project will remove the cluster including all of its data.")
    confirmed = console.confirm(question="Do you want to remove the cluster? [N/y]: ")
    if not confirmed:
        console.info("No action taken.", _exit=True)

    # delete cluster
    cluster = ctx.cluster_manager.select(id=project_id, exit_on_exception=True)
    success = cluster.delete()
    if not success:
        console.error("The cluster could not be deleted.", _exit=True)

    console.success("The project was deleted successfully.")


@click.command()
@click.pass_obj
def prune(ctx, **kwargs):
    """
    Remove unused clusters.
    """

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query {
                allProjects {
                    results {
                        id
                    }
                }
            }
            """
        )
        projects = data["allProjects"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # cluster
    cluster_list = ctx.cluster_manager.get_clusters()

    # select clusters to prune
    prune_clusters = []
    for cluster in cluster_list:
        if cluster.id not in [UUID(project["id"]) for project in projects]:
            prune_clusters.append(cluster)

    for cluster in prune_clusters:
        console.info(f"It seems like the project for cluster '{cluster.display_name}' has been deleted.")

        # delete cluster
        success = cluster.delete()
        if not success:
            console.error("The project could not be deleted.", _exit=True)

        console.success("The project was deleted successfully.")

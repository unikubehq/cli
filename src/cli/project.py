import sys
from time import sleep, time

import click
import click_spinner

import src.cli.console as console
from src import settings
from src.graphql import GraphQL
from src.helpers import check_running_cluster
from src.local.providers.types import K8sProviderType
from src.local.system import KubeAPI, Telepresence


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def list(ctx, organization, **kwargs):
    """
    Display a table of all available project names alongside with the ids.
    """

    # context
    organization_id, _, _ = ctx.context.get_context_ids_from_arguments(organization_argument=organization)

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
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
        graph_ql = GraphQL(authentication=ctx.auth)
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
@click.option(
    "--provider",
    "-p",
    help="Specify the Kubernetes provider type for this cluster (default uses k3d)",
    default=settings.UNIKUBE_DEFAULT_PROVIDER_TYPE.name,
)
@click.option("--workers", help="Specify count of k3d worker nodes", default=1)
@click.pass_obj
def up(ctx, project=None, organization=None, ingress=None, provider=None, workers=None, **kwargs):
    """
    This command starts or resumes a Kubernetes cluster for the specified project. As it is a selection command, the
    project can be specified and/or filtered in several ways:

    * as a positional argument, id or project title can be specified, or from a set context
    * as an interactive selection from available projects
    * via ``-o`` or ``--organization`` option, specifying an organisation to which a project belongs

    """

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # cluster information
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    cluster_id_list = [item.id for item in cluster_list]

    # argument
    if not project_id:
        project_id = console.project_list(ctx, organization_id=organization_id, excludes=cluster_id_list)
        if not project_id:
            return None

    if project_id in cluster_id_list:
        console.info(f"Project '{project_id}' is already up.", _exit=True)

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
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
                "id": project_id,
            },
        )
        project_selected = data["project"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    if not project_selected:
        console.info(f"The project '{project}' could not be found.", _exit=True)

    try:
        cluster_provider_type = K8sProviderType[provider]
    except KeyError:
        console.error(
            f"The provider '{provider}' is not supported. Please use "
            f"one of: {','.join(opt.name for opt in K8sProviderType)}",
            _exit=True,
        )

    check_running_cluster(ctx, cluster_provider_type, project_selected)

    # get project id
    if ingress is None:
        ingress = project_selected["clusterSettings"]["port"]

    # cluster up
    cluster_data = ctx.cluster_manager.get(id=project_selected["id"])
    cluster_data.name = project_selected["title"]
    ctx.cluster_manager.set(id=project_selected["id"], data=cluster_data)

    cluster = ctx.cluster_manager.select(cluster_data=cluster_data, cluster_provider_type=cluster_provider_type)
    console.info(
        f"Setting up a Kubernetes cluster (with provider {provider}) for " f"project '{cluster.display_name}'."
    )

    if not cluster.exists():
        console.info(f"Kubernetes cluster for '{cluster.display_name}' does not exist, creating it now.")
        with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
            success = cluster.create(
                ingress_port=ingress,
                workers=workers,
            )

    # start
    else:
        console.info(f"Kubernetes cluster for '{cluster.display_name}' already exists, starting it now.")
        with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
            success = cluster.start()

    # console
    if success:
        console.info("Now connecting Telepresence daemon. You probably have to enter your 'sudo' password.")
        provider_data = cluster.storage.get()
        k8s = KubeAPI(provider_data)
        timeout = time() + 60  # wait one minute
        while not k8s.is_available or time() > timeout:
            sleep(1)
        if not k8s.is_available:
            console.error(
                "There was an error bringing up the project cluster. The API was not available within the"
                "expiration period.",
                _exit=True,
            )
        Telepresence(cluster.storage.get()).start()
        console.success("The project cluster is up.")
    else:
        console.error("The project cluster could not be started.")


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
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)

    # argument
    if not project_id:
        project_id = console.project_list(
            ctx, organization_id=organization_id, filter=[cluster.id for cluster in cluster_list]
        )
        if not project_id:
            return None

    # check if project is in local storage
    if project_id not in [cluster.id for cluster in cluster_list]:
        console.info(f"The project cluster for '{project_id}' is not up or does not exist yet.", _exit=True)

    # get cluster
    cluster = None
    for cluster_data in cluster_list:
        if cluster_data.id == project_id:
            cluster = ctx.cluster_manager.select(
                cluster_data=cluster_data,
            )
            break

    # cluster down
    if not cluster.exists():
        # something went wrong or cluster was already delete from somewhere else
        console.info(f"No Kubernetes cluster to stop for '{cluster.display_name}'", _exit=True)

    if not cluster.ready():
        console.info(f"Kubernetes cluster for '{cluster.display_name}' is not running", _exit=True)

    console.info("Stopping Telepresence daemon.")
    Telepresence(cluster.storage.get()).stop()

    # stop cluster
    console.info(f"Stopping Kubernetes cluster for '{cluster.display_name}'")
    success = cluster.stop()

    # console
    if success:
        console.success("The project cluster is down.")
    else:
        console.error("The cluster could not be stopped.")


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def delete(ctx, project=None, organization=None, **kwargs):
    """
    Delete the current project and all related data. For further information please refer to
    :ref:`the documentation about project deletion <provision:Delete a Project>`.
    """

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

    # cluster
    cluster_list = ctx.cluster_manager.get_cluster_list()

    # argument
    if not project_id:
        project_id = console.project_list(
            ctx, organization_id=organization_id, filter=[cluster.id for cluster in cluster_list]
        )
        if not project_id:
            return None

    if project_id not in [cluster.id for cluster in cluster_list]:
        console.info(f"The project cluster for '{project}' could not be found.", _exit=True)

    # initial warning
    console.warning("Deleting a project will remove the cluster including all of its data.")

    # confirm question
    confirm = input("Do want to continue [N/y]: ")
    if confirm not in ["y", "Y", "yes", "Yes"]:
        console.info("No action taken.", _exit=True)

    # get cluster
    cluster = None
    for cluster_data in cluster_list:
        if cluster_data.id == project_id:
            cluster = ctx.cluster_manager.select(
                cluster_data=cluster_data,
            )
            break

    # delete cluster
    if not cluster.exists():
        ctx.cluster_manager.delete(cluster.id)
        console.info(f"No Kubernetes cluster to delete for '{cluster.display_name}', nothing to do.", _exit=True)

    success = cluster.delete()

    # console
    if success:
        console.success("The project was deleted successfully.")
        ctx.cluster_manager.delete(cluster.id)
    else:
        console.error("The cluster could not be deleted.")

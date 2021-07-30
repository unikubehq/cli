import re
import sys
from time import sleep

import click
import click_spinner

import src.cli.console as console
from src import settings
from src.graphql import GraphQL
from src.helpers import check_running_cluster, select_entity, select_entity_from_cluster_list, select_project_entity
from src.keycloak.permissions import KeycloakPermissions
from src.local.providers.types import K8sProviderType
from src.local.system import Telepresence
from src.storage.user import get_local_storage_user


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.pass_obj
def list(ctx, organization, **kwargs):
    """
    List all your projects.
    """

    context = ctx.context.get(organization=organization)

    # keycloak
    try:
        keycloak_permissions = KeycloakPermissions(authentication=ctx.auth)
        permission_list = keycloak_permissions.get_permissions_by_scope("project:*")
    except Exception as e:
        permission_list = None
        console.debug(e)
        console.exit_generic_error()

    # append "(active)"
    if context.project_id:
        for permission in permission_list:
            if permission.rsid == context.project_id:
                permission.rsid += " (active)"

    # console
    project_list = []
    for permission in permission_list:
        # parse name
        try:
            name = re.findall(r"project (.+?)\({rsid}\)".format(rsid=permission.rsid), permission.rsname)[0]
        except Exception:
            name = permission.rsname

        project_list.append(
            {
                "id": permission.rsid,
                "name": name,
            }
        )

    if not project_list:
        console.info("No projects available. Please go to https://app.unikube.io and create a project.", _exit=True)

    console.table(
        data=project_list,
        headers={
            "id": "Id",
            "slug": "Identifier",
            "description": "Description",
        },
    )


@click.command()
@click.argument("project", required=False)
@click.pass_obj
def info(ctx, project, **kwargs):
    """
    Display further information of the selected project.
    """

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allProjects {
                    results {
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
            }
            """
        )
    except Exception:
        data = None
        console.exit_generic_error()

    project_list = data["allProjects"]["results"]

    # argument
    if not project:
        # argument from context
        context = ctx.context.get()
        if context.project_id:
            project_instance = ctx.context.get_project()
            project = f'{project_instance["title"]} ({project_instance["organization"]["title"]})'

        # argument from console
        else:
            project = console.list(
                message="Please select a project",
                choices=[project["title"] for project in project_list],
                identifiers=[project["organization"]["title"] for project in project_list],
            )
            if project is None:
                return None

    # select
    project_selected = select_project_entity(entity_list=project_list, selection=project)

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
@click.argument("project_id", required=False)
@click.option("--remove", "-r", is_flag=True, default=False, help="Remove local organization context")
@click.pass_obj
def use(ctx, project_id, remove, **kwargs):
    """
    Set local project context.
    """

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()
    context = user_data.context

    # option: --remove
    if remove:
        user_data.context.deck_id = None
        user_data.context.project_id = None
        local_storage_user.set(user_data)
        console.success("Project context removed.")
        return None

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
                        organization {
                            id
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": context.organization_id,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    project_list = data["allProjects"]["results"]
    project_dict = {project["id"]: project for project in project_list}

    # argument
    if not project_id:
        project_title = console.list(
            message="Please select a project",
            choices=[project["title"] for project in project_dict.values()],
        )
        if project_title is None:
            return False

        for id, project in project_dict.items():
            if project["title"] == project_title:
                project_id = id

    project = project_dict.get(project_id, None)
    if not project:
        console.error(f"Unknown project with id: {project_id}.")

    # set project
    user_data.context.deck_id = None
    user_data.context.project_id = project["id"]
    user_data.context.organization_id = project["organization"]["id"]
    local_storage_user.set(user_data)

    console.success(f"Project context: {user_data.context}")


@click.command()
@click.argument("project", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--ingress", help="Specify the ingress port for the project", default=None)
@click.option(
    "--provider",
    "-p",
    help="Specify the Kubernetes provider type for this cluster",
    default=settings.UNIKUBE_DEFAULT_PROVIDER_TYPE.name,
)
@click.option("--workers", help="Specify count of k3d worker nodes", default=1)
@click.pass_obj
def up(ctx, project, organization, ingress, provider, workers, **kwargs):
    """
    Start/Resume a project cluster.
    """

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allProjects {
                    results {
                        id
                        title
                        clusterSettings {
                            id
                            port
                        }
                    }
                }
            }
            """
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    project_list = data["allProjects"]["results"]

    # argument
    if not project:
        # argument from context
        context = ctx.context.get(organization=organization)
        if context.project_id:
            project_instance = ctx.context.get_project()
            project = project_instance["title"] + f"({project_instance['id']})"

        # argument from console
        else:
            cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
            cluster_id_list = [item.id for item in cluster_list]

            project_list_choices = [
                item["title"] + f"({item['id']})" for item in project_list if item["id"] not in cluster_id_list
            ]

            project = console.list(
                message="Please select a project",
                choices=project_list_choices,
            )
            if project is None:
                return False

    project_instance = select_entity(project_list, project)
    if not project_instance:
        console.info(f"The project '{project}' could not be found.")
        return None

    try:
        cluster_provider_type = K8sProviderType[provider]
    except KeyError:
        console.error(
            f"The provider '{provider}' is not supported. Please use "
            f"one of: {','.join(opt.name for opt in K8sProviderType)}",
            _exit=True,
        )

    check_running_cluster(ctx, cluster_provider_type, project_instance)

    # get project id
    if ingress is None:
        ingress = project_instance["clusterSettings"]["port"]

    # cluster up
    cluster_data = ctx.cluster_manager.get(id=project_instance["id"])
    cluster_data.name = project_instance["title"]
    ctx.cluster_manager.set(id=project_instance["id"], data=cluster_data)

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
        sleep(5)  # todo busywait for the cluster to become actually available
        Telepresence(cluster.storage.get()).start()
        console.success("The project cluster is up.")
    else:
        console.error("The project cluster could not be started.")


@click.command()
@click.argument("project", required=False)
@click.pass_obj
def down(ctx, project, **kwargs):
    """
    Stop/Pause cluster.py
    """

    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    cluster_title_list = [item.name + f"({item.id})" for item in cluster_list]
    # import pdb;pdb.set_trace()

    # argument
    if not project:
        # argument from context
        context = ctx.context.get()
        if context.project_id:
            project_instance = ctx.context.get_project()
            project = project_instance["title"] + f"({project_instance['id']})"

        # argument from console
        else:
            project = console.list(
                message="Please select a project",
                message_no_choices="No cluster is running.",
                choices=cluster_title_list,
            )
            if project is None:
                return None

    project_instance = select_entity_from_cluster_list(cluster_list, project)

    # check if project is in local storage
    if not project_instance:
        console.info("The project cluster could not be found.")
        return None

    # get cluster
    cluster = None
    for cluster_data in cluster_list:
        if cluster_data.id == project_instance.id:
            cluster = ctx.cluster_manager.select(
                cluster_data=cluster_data,
            )
            break

    # cluster down
    if not cluster.exists():
        # something went wrong or cluster was already delete from somewhere else
        console.info(f"No Kubernetes cluster to stop for '{cluster.display_name}'")
        return None

    if not cluster.ready():
        console.info(f"Kubernetes cluster for '{cluster.display_name}' is not running")
        return None

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
@click.pass_obj
def delete(ctx, project, **kwargs):
    """Delete the current project and all related data"""

    cluster_list = ctx.cluster_manager.get_cluster_list()
    cluster_title_list = [item.name + f"({item.id})" for item in cluster_list]

    # argument
    if not project:
        # argument from context
        context = ctx.context.get()
        if context.project_id:
            project_instance = ctx.context.get_project()
            project = project_instance["title"] + f"({project_instance['id']})"

        # argument from console
        else:
            project = console.list(
                message="Please select a project",
                message_no_choices="No cluster available.",
                choices=cluster_title_list,
            )
            if project is None:
                return None

    project_instance = select_entity_from_cluster_list(cluster_list, project)

    if not project_instance:
        console.info(f"The project '{project}' could not be found.")
        return None

    # initial warning
    console.warning("Deleting a project will remove the cluster including all of its data.")

    # confirm question
    confirm = input("Do want to continue [N/y]: ")
    if confirm not in ["y", "Y", "yes", "Yes"]:
        console.info("No action taken.")
        return None

    # get cluster
    cluster = None
    for cluster_data in cluster_list:
        if cluster_data.id == project_instance.id:
            cluster = ctx.cluster_manager.select(
                cluster_data=cluster_data,
            )
            break

    # delete cluster
    if not cluster.exists():
        console.info(f"No Kubernetes cluster to delete for '{cluster.display_name}', nothing to do.")
        ctx.cluster_manager.delete(cluster.id)
        return None

    success = cluster.delete()

    # console
    if success:
        console.success("The project was deleted successfully.")
        ctx.cluster_manager.delete(cluster.id)
    else:
        console.error("The cluster could not be deleted.")

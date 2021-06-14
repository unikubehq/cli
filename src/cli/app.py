import os

import click
import click_spinner

from src import settings
from src.cli import console
from src.graphql import GraphQL
from src.local.system import Docker, KubeAPI, KubeCtl, Telepresence
from src.settings import UNIKUBE_FILE
from src.unikubefile.selector import unikube_file_selector


def get_required_information(ctx, project_title: str, deck_title: str):
    ## project_id
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    cluster_title_list = [item.name for item in cluster_list]

    # argument
    if not project_title:
        # argument from console
        project_title = console.list(
            message="Please select a project",
            message_no_choices="No cluster is running.",
            choices=cluster_title_list,
        )
        if project_title is None:
            console.exit_generic_error()

    # check if project is in local storage
    if project_title not in cluster_title_list:
        console.error("The project cluster could not be found.", _exit=True)

    # get project_id
    project_id = None
    cluster = None
    for cluster_data in cluster_list:
        if cluster_data.name == project_title:
            cluster = ctx.cluster_manager.select(
                cluster_data=cluster_data,
            )
            project_id = cluster.id
            break

    if not project_id:
        console.error("The project id could not be determined.", _exit=True)

    ## deck_id
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID) {
                allDecks(projectId: $id) {
                    results {
                        id
                        title
                        namespace
                    }
                }
            }
            """,
            query_variables={
                "id": project_id,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]
    deck_title_list = [item["title"] for item in deck_list]

    # argument
    if not deck_title:
        # argument from console
        deck_title = console.list(
            message="Please select a deck",
            message_no_choices="No deck found.",
            choices=deck_title_list,
        )
        if deck_title is None:
            console.exit_generic_error()

    # check if deck exists
    if deck_title not in deck_title_list:
        console.error("The deck could not be found.", _exit=True)

    # get deck
    deck = None
    for deck in deck_list:
        if deck["title"] == deck_title:
            break

    return project_id, project_title, deck


@click.command()
def list(**kwargs):
    raise NotImplementedError


@click.command()
def info(**kwargs):
    raise NotImplementedError


@click.command()
def use(**kwargs):
    raise NotImplementedError


@click.command()
@click.argument("project_title", required=False)
@click.argument("deck_title", required=False)
@click.argument("pod_title", required=False)
@click.pass_obj
def shell(ctx, project_title, deck_title, pod_title, **kwargs):
    """Drop into an interactive shell."""

    ctx.auth.check()

    project_id, project_title, deck = get_required_information(ctx, project_title, deck_title)

    ## shell
    # check if cluster is ready
    cluster_data = ctx.cluster_manager.get(id=project_id)
    print(project_id)
    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)
    if not cluster:
        console.error("The project cluster does not exist.")
        return None

    provider_data = cluster.storage.get()

    # shell
    k8s = KubeAPI(provider_data, deck)

    if not pod_title:
        pod_list_choices = [pod.metadata.name for pod in k8s.get_pods().items]
        pod_title = console.list(
            message="Please select a pod",
            choices=pod_list_choices,
        )

    if not pod_title:
        console.error("No pods available.")
        return None

    # get the data of the selected pod
    data = k8s.get_pod(pod_title)

    # 1. check if this pod is of a switched deployment (in case of an active Telepresence)
    if data.metadata.labels.get("telepresence"):
        # the corresponding deployment by getting rid of the telepresence suffix
        deployment = "-".join(data.metadata.name.split("-")[0:-1])

        # the container name generated in "app switch" for that pod
        container_name = settings.TELEPRESENCE_DOCKER_IMAGE_FORMAT.format(
            project=project_title, deck=deck["title"], name=deployment
        ).replace(":", "")

        if Docker().check_running(container_name):
            # 2. Connect to that container
            # 2.a connect using Docker
            Docker().exec(container_name, "/bin/sh", interactive=True)
        else:
            console.error(
                "This is a Telepresence Pod with no corresponding Docker container "
                "running in order to connect (inconsistent state?)"
            )

    else:
        # 2.b connect using kubernetes
        KubeCtl(provider_data).exec_pod(pod_title, deck["namespace"], "/bin/sh", interactive=True)


@click.command()
@click.argument("project_title", required=False)
@click.argument("deck_title", required=False)
@click.option("--deployment", help="Specify the deployment if not set in the Unikubefile")
@click.option("--image", help="Specify the Docker image from your local registry")
@click.option("--unikubefile", help="Specify the path to the Unikubefile", type=str)
@click.pass_obj
def switch(ctx, project_title, deck_title, deployment, image, unikubefile, **kwargs):
    """Switch a running deployment with a local Docker image"""

    ctx.auth.check()

    project_id, project_title, deck = get_required_information(ctx, project_title, deck_title)

    ## switch
    # check if cluster is ready
    cluster_data = ctx.cluster_manager.get(id=project_id)
    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)
    if not cluster:
        console.error("The project cluster does not exist.")
        return None

    # unikube file input
    if unikubefile:
        path_unikube_file = unikubefile
    else:
        path_unikube_file = os.path.join(os.getcwd(), UNIKUBE_FILE)

    unikube_file = unikube_file_selector.get(path_unikube_file=path_unikube_file)

    # 2: Get a deployment
    # 2.1.a Check the deployment identifier
    if not deployment:
        # 1.1.b check the unikubefile
        deployment = unikube_file.get_deployment()
        if not deployment:
            console.error("Please specify the deployment either using the '--deployment' option or in the Unikubefile")

    # 2.2 Fetch available "deployment:", deployments
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID) {
                deck(id: $id) {
                    deployments(level: "local") {
                        id
                        title
                        description
                        ports
                        isSwitchable
                    }
                }
            }
            """,
            query_variables={
                "id": deck["id"],
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    target_deployment = None

    for _deployment in data["deck"]["deployments"]:
        if _deployment["title"] == deployment:
            target_deployment = _deployment

    # 2.3 Check and select deployment data
    if target_deployment is None:
        console.error(
            f"The deployment '{deployment}' you specified could not be found.",
            _exit=True,
        )

    ports = target_deployment["ports"].split(",")
    deployment = target_deployment["title"]
    namespace = deck["namespace"]

    # 3: Build an new Docker image
    # 3.1 Grab the docker file
    context, dockerfile, target = unikube_file.get_docker_build()
    console.debug(f"{context}, {dockerfile}, {target}")
    console.info(f"Building a Docker image for {dockerfile} with context {context}")

    # 3.2 Set an image name
    image_name = settings.TELEPRESENCE_DOCKER_IMAGE_FORMAT.format(
        project=project_title.replace(" ", "").lower(), deck=deck["title"], name=deployment
    )

    # 3.3 Build image
    with click_spinner.spinner():
        status, msg = Docker().build(image_name, context, dockerfile, target)
    if not status:
        console.debug(msg)
        console.error("Failed to build Docker image.", _exit=True)

    console.info(f"Docker image successfully built: {image_name}")

    # 4. Start the Telepresence session
    # 4.1 See if there are volume mounts
    mounts = unikube_file.get_mounts()
    console.debug(f"Volumes requested: {mounts}")

    # 4.2 See if there special env variables
    envs = unikube_file.get_environment()
    console.debug(f"Envs requested: {envs}")

    # 4.3 See if there is a run command to be executed
    command = unikube_file.get_command(port=ports[0])
    console.debug(f"Run command: {command}")

    console.info("Starting your container, this may takes a while to become effective")
    provider_data = cluster.storage.get()
    Telepresence(provider_data, debug_output=True).swap(deployment, image_name, command, namespace, envs, mounts)


@click.command()
def pulldb(**kwargs):
    raise NotImplementedError


@click.command()
@click.argument("project_title", required=False)
@click.argument("deck_title", required=False)
@click.argument("pod_title", required=False)
@click.argument("pod_title", required=False)
@click.option("--watch", "-w", is_flag=True, default=False, help="Watch logs.")
@click.pass_obj
def logs(ctx, project_title, deck_title, pod_title, watch, **kwargs):
    """Display the container's logs"""

    ctx.auth.check()

    project_id, project_title, deck = get_required_information(ctx, project_title, deck_title)

    ## logs
    # check if cluster is ready
    cluster_data = ctx.cluster_manager.get(id=project_id)
    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)
    if not cluster:
        console.error("The project cluster does not exist.")
        return None

    provider_data = cluster.storage.get()

    # log
    k8s = KubeAPI(provider_data, deck)

    if not pod_title:
        pod_list_choices = [pod.metadata.name for pod in k8s.get_pods().items]
        pod_title = console.list(
            message="Please select a pod",
            choices=pod_list_choices,
        )

    if not pod_title:
        console.error("No pods available.")
        return None

    logs = k8s.get_logs(pod_title, watch)

    # output
    click.echo(logs)


@click.command()
def expose(**kwargs):
    raise NotImplementedError


@click.command()
def env(**kwargs):
    raise NotImplementedError


@click.command()
def request_env(**kwargs):
    raise NotImplementedError


@click.command()
def exec(**kwargs):
    raise NotImplementedError

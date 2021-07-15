import os
import re
import signal
import sys
from time import sleep

import click
import click_spinner

from src import settings
from src.cli import console
from src.graphql import GraphQL
from src.local.providers.helper import get_cluster_or_exit
from src.local.system import Docker, KubeAPI, KubeCtl, Telepresence
from src.settings import UNIKUBE_FILE
from src.unikubefile.selector import unikube_file_selector


def get_deck_from_arguments(ctx, organization_id: str, project_id: str, deck_id: str):

    context = ctx.context.get(organization=organization_id, project=project_id, deck=deck_id)

    ## project_id
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    cluster_choices = [f"{item.name} ({item.id})" for item in cluster_list]
    cluster_choices_ids = [item.id for item in cluster_list]

    # argument
    if not context.project_id:
        # argument from console
        project_selected = console.list(
            message="Please select a project",
            message_no_choices="No project is running.",
            choices=cluster_choices,
        )
        if project_selected is None:
            exit(1)

        project_id = re.search(r"\((.*?)\)", project_selected).group(1)
    else:
        project_id = context.project_id

    # check if project is in local storage
    if project_id not in cluster_choices_ids:
        console.error("The project cluster could not be found or you have another project activated.", _exit=True)

    cluster_data = ctx.cluster_manager.get(id=project_id)
    if not cluster_data:
        console.error("The cluster could not be found.", _exit=True)

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
                        environment {
                            namespace
                        }
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
    deck_choices = [f'{item["title"]} ({item["id"]})' for item in deck_list]
    deck_choices_ids = [item["id"] for item in deck_list]

    # argument
    if not context.deck_id:
        # argument from console
        deck_selected = console.list(
            message="Please select a deck",
            message_no_choices="No deck found.",
            choices=deck_choices,
        )
        if deck_selected is None:
            exit(1)

        deck_id = re.search(r"\((.*?)\)", deck_selected).group(1)
    else:
        deck_id = context.deck_id

    if deck_id is None:
        console.exit_generic_error()

    # check if deck exists
    if deck_id not in deck_choices_ids:
        console.error("The deck could not be found.", _exit=True)

    # get deck
    deck = None
    for deck in deck_list:
        if deck["id"] == deck_id:
            break

    return cluster_data, deck


def argument_app(k8s, app: str):
    if not app:
        app_choices = [pod.metadata.name for pod in k8s.get_pods().items]
        app = console.list(
            message="Please select an app",
            choices=app_choices,
        )

    if not app:
        console.error("No apps available.", _exit=True)

    if app not in [pod.metadata.name for pod in k8s.get_pods().items]:
        console.error("App does not exist.", _exit=True)

    return app


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def list(ctx, organization, project, deck, **kwargs):
    """List all apps/pods."""

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # list
    k8s = KubeAPI(provider_data, deck)
    pod_table = [{"id": pod.metadata.uid, "name": pod.metadata.name} for pod in k8s.get_pods().items]

    console.table(data=pod_table)


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def info(ctx, organization, project, deck, **kwargs):
    raise NotImplementedError


@click.command()
def use(**kwargs):
    raise NotImplementedError


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def shell(ctx, app, organization=None, project=None, deck=None, **kwargs):
    """Drop into an interactive shell."""

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # shell
    k8s = KubeAPI(provider_data, deck)
    app = argument_app(k8s, app)

    # get the data of the selected pod
    data = k8s.get_pod(app)

    # 1. check if this pod is of a switched deployment (in case of an active Telepresence)
    if data.metadata.labels.get("telepresence"):
        # the corresponding deployment by getting rid of the telepresence suffix
        deployment = "-".join(data.metadata.name.split("-")[0:-1])

        # the container name generated in "app switch" for that pod
        container_name = settings.TELEPRESENCE_DOCKER_IMAGE_FORMAT.format(
            project=cluster_data.name, deck=deck["title"], name=deployment
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
        KubeCtl(provider_data).exec_pod(app, deck["environment"][0]["namespace"], "/bin/sh", interactive=True)


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_context
def exec(ctx, **kwargs):
    ctx.forward(shell)


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.option("--deployment", help="Specify the deployment if not set in the Unikubefile")
@click.option("--unikubefile", help="Specify the path to the Unikubefile", type=str)
@click.pass_obj
def switch(ctx, app, organization, project, deck, deployment, unikubefile, **kwargs):
    """Switch a running deployment with a local Docker image"""

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)

    # unikube file input
    if unikubefile:
        path_unikube_file = unikubefile
    else:
        path_unikube_file = os.path.join(os.getcwd(), UNIKUBE_FILE)

    unikube_file = unikube_file_selector.get(path_unikube_file=path_unikube_file)

    # 2: Get a deployment
    # 2.1.a Check the deployment identifier
    if not deployment and unikube_file:
        # 1.1.b check the unikubefile
        deployment = unikube_file.get_deployment()
        if not deployment:
            console.error("Please specify the 'deployment' ke of your app in your unikube.yaml.", _exit=True)
    else:
        console.error(
            "Please specify the deployment either using the '--deployment' option or in the unikube.yaml. "
            "Run 'unikube app switch' in a directory containing the unikube.yaml file.",
            _exit=True,
        )

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
                    environment {
                        id
                        type
                        valuesPath
                        namespace
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
    namespace = deck["environment"][0]["namespace"]

    console.info("Please wait while unikube prepares the switch.")
    with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
        # check telepresence
        provider_data = cluster.storage.get()
        telepresence = Telepresence(provider_data)

        available_deployments = telepresence.list(namespace, flat=True)
        if deployment not in available_deployments:
            console.error(
                "The given deployment cannot be switched. " f"You may have to run 'unikube deck install {deck}' first.",
                _exit=True,
            )

        is_swapped = telepresence.is_swapped(deployment, namespace)

    # 3: Build an new Docker image
    # 3.1 Grab the docker file
    context, dockerfile, target = unikube_file.get_docker_build()
    console.debug(f"{context}, {dockerfile}, {target}")
    console.info(f"Building a Docker image for {dockerfile} with context {context}")

    # 3.2 Set an image name
    image_name = settings.TELEPRESENCE_DOCKER_IMAGE_FORMAT.format(
        project=cluster_data.name.replace(" ", "").lower(), deck=deck["title"], name=deployment
    )

    docker = Docker()

    if is_swapped:
        console.warning("It seems this app is already switched in another process. ")
        if click.confirm("Do you want to kill it and switch here?"):
            telepresence.leave(deployment, namespace, silent=True)
            if docker.check_running(image_name):
                docker.kill(name=image_name)
        else:
            sys.exit(0)

    # 3.3 Build image

    with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
        status, msg = docker.build(image_name, context, dockerfile, target)
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

    console.info("Starting your container, this may take a while to become effective")

    telepresence.swap(deployment, image_name, command, namespace, envs, mounts, ports[0])
    if docker.check_running(image_name):
        docker.kill(name=image_name)


@click.command()
def pulldb(**kwargs):
    raise NotImplementedError


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.option("--follow", "-f", is_flag=True, default=False, help="Follow logs.")
@click.pass_obj
def logs(ctx, app, organization=None, project=None, deck=None, follow=False, **kwargs):
    """Display the container's logs"""

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # log
    k8s = KubeAPI(provider_data, deck)
    app = argument_app(k8s, app)

    logs = k8s.get_logs(app, follow)

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

import os
import socket
import sys
import tempfile
from collections import OrderedDict
from typing import Tuple

import click
import click_spinner

from src import settings
from src.cli import console
from src.graphql import GraphQL
from src.local.providers.helper import get_cluster_or_exit
from src.local.system import Docker, KubeAPI, KubeCtl, Telepresence
from src.settings import UNIKUBE_FILE
from src.unikubefile.selector import unikube_file_selector


def _is_local_port_free(port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if a_socket.connect_ex(("127.0.0.1", int(port))) == 0:
        return False
    else:
        return True


def get_deck_from_arguments(ctx, organization_id: str, project_id: str, deck_id: str):
    # context
    organization_id, project_id, deck_id = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization_id, project_argument=project_id, deck_argument=deck_id
    )

    # argument
    if not deck_id:
        deck_id = console.deck_list(ctx, organization_id=organization_id, project_id=project_id)
        if not deck_id:
            exit(1)

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID) {
                deck(id: $id) {
                    id
                    title
                    environment {
                        namespace
                    }
                    project {
                        id
                    }
                }
            }
            """,
            query_variables={"id": deck_id},
        )
        deck = data["deck"]
        project_id = deck["project"]["id"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # cluster data
    cluster_list = ctx.cluster_manager.get_cluster_list(ready=True)
    if project_id not in [cluster.id for cluster in cluster_list]:
        console.info(f"The project cluster for '{project_id}' is not up or does not exist yet.", _exit=True)

    cluster_data = ctx.cluster_manager.get(id=project_id)
    if not cluster_data:
        console.error("The cluster could not be found.", _exit=True)

    return cluster_data, deck


def argument_app(k8s, app: str):
    if not app:
        app_choices = [
            pod.metadata.name
            for pod in k8s.get_pods().items
            if pod.status.phase not in ["Terminating", "Evicted", "Pending"]
        ]
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
    """List all apps."""

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # list
    k8s = KubeAPI(provider_data, deck)
    pod_table = []

    def _ready_ind(c) -> Tuple[bool, str]:
        container_count = len(c)
        ready_count = sum([val.ready for val in c])
        return container_count == ready_count, f"{ready_count}/{container_count}"

    for pod in k8s.get_pods().items:
        if pod.status.phase in ["Terminating", "Evicted", "Pending"]:
            continue
        all_ready, count = _ready_ind(pod.status.container_statuses)
        pod_table.append(
            OrderedDict({"name": pod.metadata.name, "ready": count, "state": "Ok" if all_ready else "Not Ok"})
        )
    console.table(
        data=pod_table,
        headers={
            "name": "Name",
            "ready": "Ready",
            "state": "State",
        },
    )


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def info(ctx, app, organization, project, deck, **kwargs):
    """Display the status for the given app name."""

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
    pod_status = data.status

    console.info(f"This app runs {len(pod_status.container_statuses)} container(s).")
    for idx, status in enumerate(pod_status.container_statuses):
        console.info(f"Container {idx + 1}: {status.image}")
        print("\nStartup command from workload manifest:")
        console.table(
            [
                ("Command", " ".join(data.spec.containers[idx].command) if data.spec.containers[idx].command else None),
                ("Args", " ".join(data.spec.containers[idx].args) if data.spec.containers[idx].args else None),
            ]
        )
        print("\nApp status:")
        console.table(
            [
                {"State": "Running", "Value": status.state.running.started_at if status.state.running else None},
                {
                    "State": "Terminated",
                    "Value": status.state.terminated.finished_at if status.state.terminated else None,
                },
                {"State": "Waiting", "Value": status.state.waiting.message if status.state.waiting else None},
            ]
        )

    conditions = []
    for condition in pod_status.conditions:
        conditions.append(
            OrderedDict(
                {
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "last_transition_time": condition.last_transition_time,
                    "last_probe_time": condition.last_probe_time,
                    "message": condition.message,
                }
            )
        )

    if conditions:
        conditions = sorted(conditions, key=lambda x: x.get("last_transition_time").timestamp())
        # print a line for padding on the console
        print()
        console.info("All conditions for this app:")
        console.table(
            conditions,
            headers={
                "type": "Type",
                "status": "Status",
                "reason": "Reason",
                "last_transition_time": "Time",
                "last_probe_time": "Probe Time",
                "message": "Message",
            },
        )
    else:
        console.info("No condition to display")


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def shell(ctx, app, organization=None, project=None, deck=None, **kwargs):
    """
    Drop into an interactive shell. For further information please refer to
    :ref:`the documentation about the shell <development:Get an Interactive Shell>`.
    """

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
    telepresence = Telepresence(provider_data)
    # the corresponding deployment by getting rid of the pod name suffix
    deployment = "-".join(data.metadata.name.split("-")[0:-2])
    # 1. check if this pod is of a switched deployment (in case of an active Telepresence)

    if telepresence.is_swapped(deployment):
        # the container name generated in "app switch" for that pod
        container_name = settings.TELEPRESENCE_DOCKER_IMAGE_FORMAT.format(
            project=cluster_data.name.lower(), deck=deck["title"].lower(), name=deployment.lower()
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
@click.option(
    "--no-build", "-n", is_flag=True, help="Do not build a new container image for the switch operation", default=False
)
@click.pass_obj
def switch(ctx, app, organization, project, deck, deployment, unikubefile, no_build, **kwargs):
    """
    Switch a running deployment with a local Docker container. For further information please refer to
    :ref:`the documentation about the switch operation <development:Switch Operation>`.
    """

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
            console.error("Please specify the 'deployment' key of your app in your unikube.yaml.", _exit=True)
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

        k8s = KubeAPI(provider_data, deck)
        # service account token, service cert
        service_account_tokens = k8s.get_serviceaccount_tokens(deployment)

    # 3: Build an new Docker image
    # 3.1 Grab the docker file
    context, dockerfile, target = unikube_file.get_docker_build()
    console.debug(f"{context}, {dockerfile}, {target}")

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
    if not docker.image_exists(image_name) or not no_build:
        if no_build:
            console.warning(f"Ignoring --no-build since the required image '{image_name}' does not exist")
        console.info(f"Building a Docker image for {dockerfile} with context {context}")
        with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
            status, msg = docker.build(image_name, context, dockerfile, target)
        if not status:
            console.debug(msg)
            console.error("Failed to build Docker image.", _exit=True)

        console.info(f"Docker image successfully built: {image_name}")

    # 4. Start the Telepresence session
    # 4.1 Set the right intercept port
    port = unikube_file.get_port()
    if port is None:
        port = str(ports[0])
        console.warning(
            f"No port specified although there are multiple ports available: {ports}. "
            f"Defaulting to port {port} which might not be correct."
        )
    if port not in ports:
        console.error(f"The specified port {port} is not in the rage of available options: {ports}", _exit=True)
    if not _is_local_port_free(port):
        console.error(
            f"The local port {port} is busy. Please stop the application running on " f"this port and try again.",
            _exit=True,
        )

    # 4.2 See if there are volume mounts
    mounts = unikube_file.get_mounts()
    console.debug(f"Volumes requested: {mounts}")
    # mount service tokens
    if service_account_tokens:
        tmp_sa_token = tempfile.NamedTemporaryFile(delete=True)
        tmp_sa_cert = tempfile.NamedTemporaryFile(delete=True)
        tmp_sa_token.write(service_account_tokens[0].encode())
        tmp_sa_cert.write(service_account_tokens[1].encode())
        tmp_sa_token.flush()
        tmp_sa_cert.flush()
        mounts.append((tmp_sa_token.name, settings.SERVICE_TOKEN_FILENAME))
        mounts.append((tmp_sa_cert.name, settings.SERVICE_CERT_FILENAME))
    else:
        tmp_sa_token = None
        tmp_sa_cert = None

    # 4.3 See if there special env variables
    envs = unikube_file.get_environment()
    console.debug(f"Envs requested: {envs}")

    # 4.4 See if there is a run command to be executed
    command = unikube_file.get_command(port=port)
    console.debug(f"Run command: {command}")

    console.info("Starting your container, this may take a while to become effective")

    telepresence.swap(deployment, image_name, command, namespace, envs, mounts, port)
    if docker.check_running(image_name):
        docker.kill(name=image_name)
    if tmp_sa_token:
        tmp_sa_token.close()
        tmp_sa_cert.close()


@click.command()
@click.argument("app", required=False)
@click.option("--container", "-c", help="Specify the container in this app")
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.option("--follow", "-f", is_flag=True, default=False, help="Follow the log stream.")
@click.pass_obj
def logs(ctx, app, container=None, organization=None, project=None, deck=None, follow=False, **kwargs):
    """
    Display the logs for an app. If this app contains multiple containers, specify the ``container``
    argument or choose it from the interactive selector. You can follow the log stream if you specify the
    ``-f`` flag.
    """

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # log
    k8s = KubeAPI(provider_data, deck)
    app = argument_app(k8s, app)
    # get the data of the selected pod

    if not container:
        data = k8s.get_pod(app)
        if len(data.spec.containers) > 1:
            container = console.list(
                message="Please select a container",
                message_no_choices="No container is running.",
                choices=[c.name for c in data.spec.containers],
            )
            if container is None:
                exit(1)

    logs = k8s.get_logs(app, follow, container=container)

    # output
    click.echo(logs)


@click.command()
@click.argument("app", required=False)
@click.option("--init", "-i", is_flag=True, help="Display environment variables for the init container", default=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def env(ctx, app, init, organization, project, deck, **kwargs):
    """
    Display the environment variables for the given app. This prints the environment variables for all containers. You
    can print the environment variables for all init containers with the ``-i`` flag.
    """

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # env
    k8s = KubeAPI(provider_data, deck)
    app = argument_app(k8s, app)

    # get the data of the selected pod
    data = k8s.get_pod(app)

    if init:
        containers = data.spec.init_containers
    else:
        containers = data.spec.containers

    if containers:

        console.info(f"This app runs {len(containers)} container(s).")
        for idx, container in enumerate(containers):
            console.info(f"Container {idx + 1}: {container.image}")
            env_vars = []

            def _value_from(s) -> Tuple[str, str]:
                # return an indicator if this values comes from a secret and the name
                if s.config_map_key_ref:
                    return "ConfigMap", s.config_map_key_ref
                elif s.field_ref and s.field_ref.field_path:
                    return "Field", s.field_ref.field_path
                elif s.resource_field_ref:
                    return "ResourceField", s.resource_field_ref
                elif s.secret_key_ref and s.secret_key_ref.name:
                    return "Secret", f"Secret: {s.secret_key_ref.name} Key: {s.secret_key_ref.key}"

            for env in container.env:
                if env.value_from:
                    type, source = _value_from(env.value_from)
                else:
                    type, source = "Definition", "-"
                env_vars.append(
                    OrderedDict(
                        {
                            "name": env.name,
                            "value": env.value,
                            "source_type": type,
                            "path": source,
                        }
                    )
                )
            console.table(
                env_vars,
                headers={
                    "name": "Name",
                    "value": "Value",
                    "path": "Path",
                    "source_type": "Source Type",
                },
            )
    else:
        console.info("No container running")


@click.command()
@click.argument("app", required=False)
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def update(ctx, app, organization, project, deck, **kwargs):
    """
    Trigger a forced update of the given app. This command creates a new app instance.
    """

    ctx.auth.check()
    cluster_data, deck = get_deck_from_arguments(ctx, organization, project, deck)

    # get cluster
    cluster = get_cluster_or_exit(ctx, cluster_data.id)
    provider_data = cluster.storage.get()

    # delete pod
    k8s = KubeAPI(provider_data, deck)
    app = argument_app(k8s, app)
    k8s.delete_pod(app)
    console.info(f"The app {app} is currently updating and does not exist anymore.")

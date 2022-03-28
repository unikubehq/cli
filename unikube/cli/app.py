import sys
from collections import OrderedDict
from typing import List, Tuple

import click
import click_spinner

from unikube.cli import console
from unikube.cli.helper import age_from_timestamp
from unikube.cluster.system import Docker, KubeAPI, KubeCtl
from unikube.graphql_utils import GraphQL
from unikube.unikubefile.selector import unikube_file_selector


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
        graph_ql = GraphQL(cache=ctx.cache)
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
            query_variables={"id": str(deck_id)},
        )
        deck = data["deck"]
        project_id = deck["project"]["id"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    return project_id, deck


def argument_apps(k8s, apps: List[str], multiselect: bool = False) -> List[str]:
    if not apps:
        app_choices = [
            pod.metadata.name
            for pod in k8s.get_pods().items
            if pod.status.phase not in ["Terminating", "Evicted", "Pending"]
        ]
        message = "Please select an app" if not multiselect else "Please select one or multiple apps"
        kwargs = {
            "message": message,
            "choices": app_choices,
            "multiselect": multiselect,
        }
        if multiselect:
            kwargs["transformer"] = lambda result: f"{', '.join(result)}"
            apps = console.list(**kwargs)
        else:
            apps = [console.list(**kwargs)]

    if not apps:
        console.error("No apps available.", _exit=True)

    if apps and any(c_app not in [pod.metadata.name for pod in k8s.get_pods().items] for c_app in apps):
        console.error("Some apps do not exist.", _exit=True)

    return apps


def argument_app(k8s, app: str) -> str:
    return argument_apps(k8s, [app] if app else [])[0]


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def list(ctx, organization, project, deck, **kwargs):
    """List all apps."""

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # list
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
    pod_table = []

    def _ready_ind(c) -> Tuple[bool, str]:
        # get container count
        if c is None:
            container_count = 0
            ready_count = 0
        else:
            container_count = len(c)
            ready_count = sum([val.ready for val in c])
        return container_count == ready_count, f"{ready_count}/{container_count}"

    for pod in k8s.get_pods().items:
        if pod.status.phase in ["Terminating", "Evicted", "Pending"]:
            continue
        all_ready, count = _ready_ind(pod.status.container_statuses)
        pod_table.append(
            OrderedDict(
                {
                    "name": pod.metadata.name,
                    "ready": count,
                    "state": "Ok" if all_ready else "Not Ok",
                    "age": age_from_timestamp(pod.metadata.creation_timestamp.timestamp()),
                }
            )
        )
    console.table(
        data=pod_table,
        headers={
            "name": "Name",
            "ready": "Ready",
            "state": "State",
            "age": "Age",
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

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # shell
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
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
@click.option("--container", "-c", help="Specify the container in this app")
@click.pass_obj
def shell(ctx, app, organization=None, project=None, deck=None, container=None, **kwargs):
    """
    Drop into an interactive shell.
    """

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # shell
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
    app = argument_app(k8s, app)

    # get the data of the selected pod
    data = k8s.get_pod(app)

    # the corresponding deployment by getting rid of the pod name suffix
    deployment = "-".join(data.metadata.name.split("-")[0:-2])

    # 1. check if this pod is of a switched deployment
    if cluster.bridge.is_switched(deployment=deployment, namespace=data.metadata.namespace):
        # the container name generated in "app switch" for that pod
        image_name = cluster.bridge.get_docker_image_name(deployment=deployment)

        if Docker().check_running(image_name):
            # 2. connect to that container using Docker
            Docker().exec(image_name, "/bin/sh", interactive=True)
        else:
            console.error(
                "This is a switched app with no corresponding docker container (inconsistent state?).", _exit=True
            )

    else:
        if not container and len(data.spec.containers) > 1:
            container = console.container_list(data=data)
            if not container:
                return None

        # 2.b connect using kubernetes
        KubeCtl(cluster.get_kubeconfig_path()).exec_pod(
            app, deck["environment"][0]["namespace"], "/bin/sh", interactive=True, container=container
        )


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
@click.option("--unikube-file", help="Specify the path to the Unikubefile", type=str)
@click.option(
    "--no-build", "-n", is_flag=True, help="Do not build a new container image for the switch operation", default=False
)
@click.pass_obj
def switch(ctx, app, organization, project, deck, unikube_file: str = None, no_build: bool = False, **kwargs):
    """
    Switch a running deployment with a local Docker container.
    """

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # unikube file
    try:
        unikube_file = unikube_file_selector.get(path_unikube_file=unikube_file)
        unikube_file_app = unikube_file.get_app(name=app)
    except Exception as e:
        console.debug(e)
        console.error("Invalid unikube file 'app' argument.", _exit=True)

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
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
                "id": str(deck["id"]),
            },
        )
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # select target deployment
    deployment = unikube_file_app.get_deployment()
    for target_deployment in data["deck"]["deployments"]:
        if target_deployment["title"] == deployment:
            break
    else:
        console.error(f"The deployment '{deployment}' you specified could not be found.", _exit=True)

    namespace = deck["environment"][0]["namespace"]
    ports = target_deployment["ports"].split(",")

    # check if deployment exists
    with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
        # TODO:
        # available_deployments = cluster.bridge.list(namespace, flat=True)
        # if deployment not in available_deployments:
        #     console.error(
        #         "The given deployment cannot be switched. " f"You may have to run 'unikube deck install {deck}' first.",
        #         _exit=True,
        #     )
        pass

    # build a (new) docker image
    console.info("Please wait while unikube prepares the switch.")
    cluster.bridge.build(deployment, namespace, unikube_file_app, no_build)

    # start switch operation
    console.info(f"Starting your {cluster.cluster_bridge_type} bridge, this may take a while to become effective")
    cluster.bridge.switch(
        kubeconfig_path=cluster.get_kubeconfig_path(),
        deployment=deployment,
        namespace=namespace,
        ports=ports,
        unikube_file_app=unikube_file_app,
    )


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

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # log
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
    app = argument_app(k8s, app)

    # get the data of the selected pod
    if not container:
        data = k8s.get_pod(app)
        if len(data.spec.containers) > 1:
            container = console.container_list(data=data)
            if not container:
                return None

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

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # env
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
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

            if container.env:
                for env in container.env:
                    if env.value_from:
                        type, source = _value_from(env.value_from)
                    else:
                        type, source = "Definition", "-"
                    env_vars.append(
                        OrderedDict(
                            {
                                "name": env.name,
                                "value": str(env.value[:50]) + "..."
                                if env.value and len(env.value) > 50
                                else env.value,
                                "source_type": type,
                                "path": source,
                            }
                        )
                    )
            if container.env_from:
                for env in container.env_from:
                    if env.config_map_ref:
                        _cm = k8s.get_configmap(env.config_map_ref.name)
                        if _cm.data:
                            for k, v in _cm.data.items():
                                env_vars.append(
                                    OrderedDict(
                                        {
                                            "name": k,
                                            "value": str(v[:50]) + "..." if v and len(v) > 50 else v,
                                            "source_type": "ConfigMap",
                                            "path": _cm.metadata.name,
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

    cluster_id, deck = get_deck_from_arguments(ctx, organization, project, deck)
    cluster = ctx.cluster_manager.select(id=cluster_id, exit_on_exception=True)

    # delete pod
    k8s = KubeAPI(kubeconfig_path=cluster.get_kubeconfig_path(), deck=deck)
    apps = argument_apps(k8s, [app] if app else [], multiselect=True)
    [k8s.delete_pod(app) for app in apps]
    console.info(f"The app(s) {', '.join(apps)} are currently updating and do not exist anymore.")

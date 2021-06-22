import click

import src.cli.console as console
from src.cli.app import get_deck_from_arguments
from src.cli.console.logger import LogLevel, color_mapping
from src.graphql import EnvironmentType, GraphQL
from src.helpers import check_environment_type_local_or_exit, download_manifest, environment_type_from_string
from src.local.system import KubeAPI, KubeCtl
from src.storage.user import get_local_storage_user


def get_install_uninstall_arguments(ctx, deck_title: str):
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allDecks(limit:100) {
                    totalCount
                    results {
                        id
                        title
                        namespace
                        environment {
                            id
                            type
                            valuesPath
                        }
                        project {
                            id
                            title
                            organization {
                                title
                            }
                        }
                    }
                }
            }
            """,
            query_variables={},
        )

    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]

    # argument
    if not deck_title:
        # argument from context
        context = ctx.context.get()
        if context.deck_id:
            deck = ctx.context.get_deck()
            deck_title = deck["title"]

        # argument from console
        else:
            deck_list_choices = [item["title"] for item in deck_list]
            deck_title = console.list(
                message="Please select a deck",
                choices=deck_list_choices,
            )
            if deck_title is None:
                exit(1)

    # check access to the deck
    deck_title_list = [deck["title"] for deck in deck_list]
    if deck_title not in deck_title_list:
        console.error(f"The deck '{deck_title}' could not be found.")
        exit(1)

    # get deck
    deck_selected = None
    for deck in deck_list:
        if deck["title"] == deck_title:
            deck_selected = deck
            break

    return deck_selected


def get_cluster(ctx, deck: dict):
    cluster_data = ctx.cluster_manager.get(id=deck["project"]["id"])
    if not cluster_data.name:
        console.error_and_exit("The project cluster does not exist. Please be sure to run 'unikube project up' first.")

    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)

    # check if kubernetes cluster is running/ready
    if not cluster.ready():
        console.error_and_exit(f"Kubernetes cluster for '{cluster.display_name}' is not running.")

    return cluster


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.pass_obj
def list(ctx, organization=None, project=None, **kwargs):
    """
    List all decks.
    """

    context = ctx.context.get(organization=organization, project=project)

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID, $project_id: UUID) {
                allDecks(organizationId: $organization_id, projectId: $project_id) {
                    results {
                        id
                        title
                        project {
                            title
                            organization {
                                title
                            }
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": organization,
                "project_id": project,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]
    if not deck_list:
        console.info("No decks available. Please go to https://app.unikube.io and create a project.")
        exit(0)

    # format list to table
    table_data = []
    for deck in deck_list:
        data = {}

        if not context.organization_id:
            data["organization"] = deck["project"]["organization"]["title"]

        if not context.project_id:
            data["project"] = deck["project"]["title"]

        data["id"] = deck["id"]
        data["title"] = deck["title"]
        table_data.append(data)

    # console
    console.table(data=table_data)


@click.command()
@click.argument("deck_name", required=False)
@click.pass_obj
def info(ctx, deck_name, **kwargs):
    """
    Display further information of the selected deck.
    """

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allDecks {
                    results {
                        id
                        title
                        description
                        namespace
                        type
                    }
                }
            }
            """
        )
    except Exception:
        data = None
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]

    # argument
    if not deck_name:
        # argument from context
        context = ctx.context.get()
        if context.deck_id:
            deck = ctx.context.get_deck()
            deck_name = deck["title"]

        # argument from console
        else:
            deck_name = console.list(
                message="Please select a deck",
                choices=[deck["title"] for deck in deck_list],
            )
            if deck_name is None:
                return None

    # select
    deck_selected = None
    for deck in deck_list:
        if deck["title"] == deck_name:
            deck_selected = deck
            break

    # console
    if deck_selected:
        console.table(
            data={
                "key": [k for k in deck_selected.keys()],
                "value": [v for v in deck_selected.values()],
            },
            headers=["Key", "Value"],
        )
    else:
        console.error("Deck does not exist.")


@click.command()
@click.argument("deck_id", required=False)
@click.option("--remove", "-r", is_flag=True, default=False, help="Remove local deck context")
@click.pass_obj
def use(ctx, deck_id, remove, **kwargs):
    """
    Set local deck context.
    """

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()
    context = user_data.context

    # option: --remove
    if remove:
        user_data.context.deck_id = None
        local_storage_user.set(user_data)
        console.success("Deck context removed.")
        return None

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID, $project_id: UUID) {
                allDecks(organizationId: $organization_id, projectId: $project_id) {
                    results {
                        title
                        id
                        project {
                            id
                            organization {
                                id
                            }
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": context.organization_id,
                "project_id": context.project_id,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]
    deck_dict = {deck["id"]: deck for deck in deck_list}

    # argument
    if not deck_id:
        deck_title = console.list(
            message="Please select a deck",
            choices=[deck["title"] for deck in deck_dict.values()],
        )
        if deck_title is None:
            return False

        for id, deck in deck_dict.items():
            if deck["title"] == deck_title:
                deck_id = id

    deck = deck_dict.get(deck_id, None)
    if not deck:
        console.error(f"Unknown deck with id: {deck_id}.")

    # set deck
    user_data.context.organization_id = deck["project"]["organization"]["id"]
    user_data.context.project_id = deck["project"]["id"]
    user_data.context.deck_id = deck["id"]
    local_storage_user.set(user_data)

    console.success(f"Deck context: {user_data.context}")


@click.command()
@click.argument("deck_title", required=False)
@click.pass_obj
def install(ctx, deck_title, **kwargs):
    """
    Install deck.
    """

    deck = get_install_uninstall_arguments(ctx=ctx, deck_title=deck_title)

    # cluster
    cluster = get_cluster(ctx=ctx, deck=deck)

    # check environment type
    check_environment_type_local_or_exit(deck=deck)

    # download manifest
    general_data = ctx.storage_general.get()
    manifest = download_manifest(deck=deck, access_token=general_data.authentication.access_token)

    # KubeCtl
    provider_data = cluster.storage.get()
    kubectl = KubeCtl(provider_data=provider_data)
    namespace = deck["namespace"]
    kubectl.create_namespace(namespace)
    with click.progressbar(
        manifest,
        label="[INFO] Installing Kubernetes resources to the cluster.",
    ) as files:
        for file in files:
            kubectl.apply_str(namespace, file["content"])

    ingresss = KubeAPI(provider_data, deck).get_ingress()
    ingress_data = []
    for ingress in ingresss.items:
        hosts = []
        paths = []
        for rule in ingress.spec.rules:
            hosts.append(f"http://{rule.host}:{provider_data.publisher_port}")  # NOSONAR
            for path in rule.http.paths:
                paths.append(f"{path.path} -> {path.backend.service_name}")
                # this is an empty line in output
            hosts.append("")
            paths.append("")

        ingress_data.append(
            {
                "name": ingress.metadata.name,
                "url": "\n".join(hosts),
                "paths": "\n".join(paths),
            }
        )

    # console
    console.table(
        ingress_data,
        headers={"name": "Name", "url": "URLs"},
    )


@click.command()
@click.argument("deck_title", required=False)
@click.pass_obj
def uninstall(ctx, deck_title, **kwargs):
    """
    Uninstall deck.
    """

    deck = get_install_uninstall_arguments(ctx=ctx, deck_title=deck_title)

    # cluster
    cluster = get_cluster(ctx=ctx, deck=deck)

    # check environment type
    check_environment_type_local_or_exit(deck=deck)

    # download manifest
    general_data = ctx.storage_general.get()
    manifest = download_manifest(deck=deck, access_token=general_data.authentication.access_token)

    # KubeCtl
    provider_data = cluster.storage.get()
    kubectl = KubeCtl(provider_data=provider_data)
    namespace = deck["namespace"]
    with click.progressbar(
        manifest,
        label="[INFO] Deleting Kubernetes resources.",
    ) as files:
        for file in files:
            kubectl.delete_str(namespace, file["content"])

    # console
    console.success("Deck deleted.")


@click.command()
@click.argument("project_title", required=False)
@click.argument("deck_title", required=False)
@click.pass_obj
def logs(ctx, project_title, deck_title, **kwargs):
    """Display the container's logs"""

    ctx.auth.check()

    project_id, project_title, deck = get_deck_from_arguments(ctx, project_title, deck_title)

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
    for pod_name in [pod.metadata.name for pod in k8s.get_pods().items]:
        # get logs
        logs = k8s.get_logs(pod_name, follow=False)

        # output
        fg = color_mapping.get(LogLevel.SUCCESS, "")
        click.secho(f"[APP] {pod_name}", fg=fg)
        click.echo(logs)


@click.command()
@click.argument("deck_name", required=False)
@click.option("--app", "-a", help="Request a new environment variable")
def request_env(deck_name, **kwargs):
    raise NotImplementedError

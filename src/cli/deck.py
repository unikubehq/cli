import click

import src.cli.console as console
from src.graphql import GraphQL
from src.helpers import check_environment_type_local_or_exit, download_manifest, select_entity
from src.local.system import KubeAPI, KubeCtl
from src.storage.user import get_local_storage_user


def get_install_uninstall_arguments(ctx, deck: str):
    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()
    context = user_data.context

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID, $project_id: UUID) {
                allDecks(organizationId: $organization_id, projectId: $project_id, limit: 100) {
                    totalCount
                    results {
                        id
                        title
                        environment {
                            id
                            type
                            valuesPath
                            namespace
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

    # argument
    if not deck:
        # argument from context
        context = ctx.context.get()
        if context.deck_id:
            deck_instance = ctx.context.get_deck()
            deck = deck_instance["title"] + f"({deck_instance['id']})"

        # argument from console
        else:
            deck_list_choices = [item["title"] + f"({item['id']})" for item in deck_list]
            deck = console.list(
                message="Please select a deck",
                choices=deck_list_choices,
            )
            if deck is None:
                exit(1)
    # get deck from duplicates
    deck_selected = select_entity(deck_list, deck)
    if not deck_selected:
        console.error(f"The deck '{deck}' could not be found.", _exit=True)
    return deck_selected


def get_cluster(ctx, deck: dict):
    cluster_data = ctx.cluster_manager.get(id=deck["project"]["id"])
    if not cluster_data.name:
        console.error(
            "The project cluster does not exist. Please be sure to run 'unikube project up' first.", _exit=True
        )

    cluster = ctx.cluster_manager.select(cluster_data=cluster_data)

    # check if kubernetes cluster is running/ready
    if not cluster.ready():
        console.error(f"The project cluster for '{cluster.display_name}' is not running.", _exit=True)

    return cluster


def get_ingress_data(deck, provider_data):
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
    return ingress_data


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
                "organization_id": context.organization_id,
                "project_id": context.project_id,
            },
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]
    if not deck_list:
        console.warning("No decks available. Please go to https://app.unikube.io and create a project.", _exit=True)

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
@click.argument("deck", required=False)
@click.pass_obj
def info(ctx, deck, **kwargs):
    """
    Display further information of the selected deck.
    """

    context = ctx.context.get()

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
                        description
                        namespace
                        type
                    }
                }
            }
            """,
            query_variables={
                "organization_id": context.organization_id,
                "project_id": context.project_id,
            },
        )
    except Exception:
        data = None
        console.exit_generic_error()

    deck_list = data["allDecks"]["results"]

    # argument
    if not deck:
        # argument from context
        context = ctx.context.get()
        if context.deck_id:
            deck_instance = ctx.context.get_deck()
            deck = deck_instance["title"] + f"({deck_instance['id']})"

        # argument from console
        else:
            deck = console.list(
                message="Please select a deck",
                choices=[deck["title"] + f"({deck['id']})" for deck in deck_list],
            )
            if deck is None:
                return None

    # select
    deck_selected = select_entity(deck_list, deck)

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
        console.error(f"Unknown deck with id: {deck_id}.", _exit=True)

    # set deck
    user_data.context.organization_id = deck["project"]["organization"]["id"]
    user_data.context.project_id = deck["project"]["id"]
    user_data.context.deck_id = deck["id"]
    local_storage_user.set(user_data)

    console.success(f"Deck context: {user_data.context}")


@click.command()
@click.argument("deck", required=False)
@click.pass_obj
def install(ctx, deck, **kwargs):
    """
    Install a deck.
    """

    deck = get_install_uninstall_arguments(ctx=ctx, deck=deck)

    # cluster
    cluster = get_cluster(ctx=ctx, deck=deck)

    # check environment type
    check_environment_type_local_or_exit(deck=deck)

    # download manifest
    general_data = ctx.storage_general.get()
    manifest = download_manifest(
        deck=deck, authentication=ctx.auth, access_token=general_data.authentication.access_token
    )

    # KubeCtl
    provider_data = cluster.storage.get()
    kubectl = KubeCtl(provider_data=provider_data)
    namespace = deck["environment"][0]["namespace"]
    kubectl.create_namespace(namespace)
    with click.progressbar(
        manifest,
        label="[INFO] Installing Kubernetes resources to the cluster.",
    ) as files:
        for file in files:
            kubectl.apply_str(namespace, file["content"])

    ingress_data = get_ingress_data(deck, provider_data)

    # console
    console.table(
        ingress_data,
        headers={"name": "Name", "url": "URLs", "paths": "Paths"},
    )


@click.command()
@click.argument("deck", required=False)
@click.pass_obj
def uninstall(ctx, deck, **kwargs):
    """
    Uninstall a deck.
    """

    deck = get_install_uninstall_arguments(ctx=ctx, deck=deck)

    # cluster
    cluster = get_cluster(ctx=ctx, deck=deck)

    # check environment type
    check_environment_type_local_or_exit(deck=deck)

    # download manifest
    general_data = ctx.storage_general.get()
    manifest = download_manifest(
        deck=deck, authentication=ctx.auth, access_token=general_data.authentication.access_token
    )

    # KubeCtl
    provider_data = cluster.storage.get()
    kubectl = KubeCtl(provider_data=provider_data)
    namespace = deck["environment"][0]["namespace"]
    with click.progressbar(
        manifest,
        label="[INFO] Deleting Kubernetes resources.",
    ) as files:
        for file in files:
            kubectl.delete_str(namespace, file["content"])

    # console
    console.success("Deck deleted.")


@click.command()
@click.argument("deck", required=False)
@click.pass_obj
def ingress(ctx, deck, **kwargs):
    """
    Display ingress configuration for *installed* decks. This command prints a table containing URLs, paths and
    the associated backends.
    """
    deck = get_install_uninstall_arguments(ctx=ctx, deck=deck)

    # get cluster
    cluster = get_cluster(ctx=ctx, deck=deck)
    provider_data = cluster.storage.get()

    ingress_data = get_ingress_data(deck, provider_data)
    console.table(
        ingress_data,
        headers={"name": "Name", "url": "URLs"},
    )

    if not ingress_data:
        console.warning(
            f"Are you sure the deck is installed? You may have to run 'unikube deck install {deck['title']}' first."
        )

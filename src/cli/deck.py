import click

import src.cli.console as console
from src.graphql import GraphQL
from src.helpers import check_environment_type_local_or_exit, download_manifest
from src.local.system import KubeAPI, KubeCtl


def get_deck(ctx, deck_id: str):
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
            """,
            query_variables={"id": deck_id},
        )
        deck = data["deck"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    return deck


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

    # context
    organization_id, project_id, _ = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project
    )

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
                "organization_id": organization_id,
                "project_id": project_id,
            },
        )
        deck_list = data["allDecks"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    if not deck_list:
        console.warning("No decks available. Please go to https://app.unikube.io and create a project.", _exit=True)

    # format list to table
    table_data = []
    for deck in deck_list:
        data = {}

        if not organization_id:
            data["organization"] = deck["project"]["organization"]["title"]

        if not project_id:
            data["project"] = deck["project"]["title"]

        data["id"] = deck["id"]
        data["title"] = deck["title"]
        table_data.append(data)

    # console
    console.table(data=table_data)


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.argument("deck", required=False)
@click.pass_obj
def info(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Display further information of the selected deck.
    """

    # context
    organization_id, project_id, deck_id = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project, deck_argument=deck
    )

    # argument
    if not deck_id:
        deck_id = console.deck_list(ctx, organization_id=organization_id, project_id=project_id)
        if not deck_id:
            return None

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($id: UUID) {
                deck(id: $id) {
                    id
                    title
                    description
                    namespace
                    type
                }
            }
            """,
            query_variables={"id": deck_id},
        )
        deck_selected = data["deck"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

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
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.argument("deck", required=False)
@click.pass_obj
def install(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Install a deck. For further information please refer to
    :ref:`
    """

    # context
    organization_id, project_id, deck_id = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project, deck_argument=deck
    )

    # argument
    if not deck_id:
        deck_id = console.deck_list(ctx, organization_id=organization_id, project_id=project_id)
        if not deck_id:
            return None

    deck = get_deck(ctx, deck_id=deck_id)

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

    # ingress
    ingress_data = get_ingress_data(deck, provider_data)
    if not ingress_data:
        console.info("No ingress configuration available.", _exit=True)

    console.table(
        ingress_data,
        headers={"name": "Name", "url": "URLs", "paths": "Paths"},
    )


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.argument("deck", required=False)
@click.pass_obj
def uninstall(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Uninstall a deck. For further information please refer to
    :ref:`the documentation about deck uninstallation <provision:Deck Uninstallation>`.
    """

    # context
    organization_id, project_id, deck_id = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project, deck_argument=deck
    )

    # argument
    if not deck_id:
        deck_id = console.deck_list(ctx, organization_id=organization_id, project_id=project_id)
        if not deck_id:
            return None

    deck = get_deck(ctx, deck_id=deck_id)

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
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.argument("deck", required=False)
@click.pass_obj
def ingress(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Display ingress configuration for *installed* decks. This command prints a table containing URLs, paths and
    the associated backends.
    """

    # context
    organization_id, project_id, deck_id = ctx.context.get_context_ids_from_arguments(
        organization_argument=organization, project_argument=project, deck_argument=deck
    )

    # argument
    if not deck_id:
        deck_id = console.deck_list(ctx, organization_id=organization_id, project_id=project_id)
        if not deck_id:
            return None

    deck = get_deck(ctx, deck_id=deck_id)

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

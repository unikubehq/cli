import re
import sys
from urllib.parse import urljoin

import click_spinner
import pkg_resources
import requests
from requests import HTTPError, Session

import src.cli.console as console
from src import settings
from src.authentication.authentication import TokenAuthentication
from src.context import ClickContext
from src.graphql import EnvironmentType
from src.local.providers.types import K8sProviderType
from src.local.system import Telepresence


def select_entity(entity_list, identifier):
    # parsing id, which should be in parentheses after the project title
    id = re.search("(?<=\\()[^)]*(?=\\))", identifier)
    similar_entities = []
    if id:
        identifier = id.group(0)
    for entity in entity_list:
        if identifier == entity.get("id"):
            return entity
        elif identifier in (entity.get("title"), entity.get("slug")):
            similar_entities.append(entity)
    if len(similar_entities) > 1:
        console.warning(
            f"Entity {similar_entities[0].get('title')} has a duplicate title or slug. Specify ID directly "
            f"after title or slug in parentheses."
        )
        return None
    elif len(similar_entities) == 1:
        return similar_entities[0]
    else:
        console.warning(f"Entity {identifier} was not found.")
        return None


def select_entity_from_cluster_list(cluster_list, identifier):
    # parsing id, which should be in parentheses after the project title
    id = re.search("(?<=\\()[^)]*(?=\\))", identifier)
    similar_entities = []
    if id:
        identifier = id.group(0)
    for entity in cluster_list:
        if identifier == entity.id:
            return entity
        elif (hasattr(entity, "slug") and identifier == entity.slug) or (identifier == entity.name):
            similar_entities.append(entity)
    if len(similar_entities) > 1:
        console.warning(
            f"Entity {similar_entities[0].name} has a duplicate title or slug. Specify ID directly "
            f"after title or slug in parentheses."
        )
        return None
    elif len(similar_entities) == 1:
        return similar_entities[0]
    else:
        console.warning(f"Entity {identifier} was not found.")
        return None


def get_requests_session(access_token) -> Session:
    session = requests.Session()
    session.headers.update({"Content-type": "application/json", "Authorization": "Bearer " + str(access_token)})
    return session


def download_specs(access_token: str, environment_id: str):
    session = get_requests_session(access_token=access_token)

    manifest_url = urljoin(settings.MANIFEST_DEFAULT_HOST, environment_id)
    with click_spinner.spinner(beep=False, disable=False, force=False, stream=sys.stdout):
        response = session.get(manifest_url)
    response.raise_for_status()

    manifest = response.json()
    return manifest


def download_manifest(deck: dict, authentication: TokenAuthentication, access_token: str, environment_index: int = 0):
    try:
        environment_id = deck["environment"][environment_index]["id"]
        console.info("Requesting manifests. This process may take a few seconds.")
        manifest = download_specs(
            access_token=access_token,
            environment_id=environment_id,
        )
    except HTTPError as e:
        project_id = deck["project"]["id"]
        if e.response.status_code == 404:
            console.warning(
                "This deck does potentially not specify a valid Environment of type 'local'. "
                f"Please go to https://app.unikube.io/project/{project_id}/decks "
                f"and save a valid values path."
            )
            exit(1)
        elif e.response.status_code == 403:
            console.warning("Refreshing access token")
            environment_id = deck["environment"][environment_index]["id"]
            response = authentication.refresh()
            if not response["success"]:
                console.exit_login_required()

            access_token = response["response"]["access_token"]
            try:
                manifest = download_specs(
                    access_token=access_token,
                    environment_id=environment_id,
                )
            except HTTPError as e:
                console.warning(f"Even after refreshing access token download specs fails with {e}")
                exit(1)
        else:
            console.error("Could not load manifest: " + str(e), _exit=True)

    return manifest


# environment
def environment_type_from_string(environment_type: str):
    try:
        environment_type = EnvironmentType(environment_type)
    except Exception as e:
        console.debug(e)
        environment_type = None

    return environment_type


def check_environment_type_local_or_exit(deck: dict, environment_index: int = 0):
    if (
        environment_type_from_string(environment_type=deck["environment"][environment_index]["type"])
        != EnvironmentType.LOCAL
    ):
        console.error("This deck cannot be installed locally.", _exit=True)


def check_running_cluster(ctx: ClickContext, cluster_provider_type: K8sProviderType.k3d, project_instance: dict):
    for cluster_data in ctx.cluster_manager.get_all():
        cluster = ctx.cluster_manager.select(cluster_data=cluster_data, cluster_provider_type=cluster_provider_type)
        if cluster.exists() and cluster.ready():
            if cluster.name == project_instance["title"] and cluster.id == project_instance["id"]:
                Telepresence(cluster.storage.get()).start()
                console.info(f"Kubernetes cluster for '{cluster.display_name}' is already running.", _exit=True)
            else:
                console.error(
                    f"You cannot start multiple projects at the same time. Project {cluster.name}({cluster.id}) is "
                    f"currently running. Please run 'unikube project down \"{cluster.name}({cluster.id})\"' first and "
                    f"try again.",
                    _exit=True,
                )


def compare_current_and_latest_versions():
    try:
        current_version = pkg_resources.require("unikube")[0].version
    except pkg_resources.DistributionNotFound as e:
        console.warning(f"Version of the package could not be found: {e}")
    else:
        all_releases = requests.get("https://api.github.com/repos/unikubehq/cli/releases")
        latest_release_version = all_releases.json()[0]["tag_name"].replace("-", ".")
        if current_version != latest_release_version:
            console.info(
                f"You are using unikube version {current_version}; however, version {latest_release_version} is available."
            )


def get_organization_id_by_title(graph_ql, organization):
    organization_id = None
    organization_list = graph_ql.query(
        """
        {
            allOrganizations {
                results {
                    id
                    title
                }
            }
        }
        """
    )
    for orga in organization_list["allOrganizations"]["results"]:
        if orga["title"] == organization:
            organization_id = orga["id"]
    return organization_id


def get_list_of_project_ids_by_organization_id(graph_ql, organization_id):
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
            "organization_id": organization_id,
        },
    )
    project_ids = [project["id"] for project in data["allProjects"]["results"]]
    return project_ids


def get_projects_by_organization_id(graph_ql, organization_id):
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
            "organization_id": organization_id,
        },
    )
    return data

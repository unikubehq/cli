import re
import sys
from urllib.parse import urljoin

import click_spinner
import requests
from requests import HTTPError, Session

from src import settings
from src.cli import console
from src.graphql import EnvironmentType


def select_entity(entity_list, identifier):
    # parsing id, which should be in parentheses after the project title
    id = re.search("(?<=\\()[^)]*(?=\\))", identifier)
    if id:
        identifier = id.group(0)
    for entity in entity_list:
        if identifier in (entity.get("id"), entity.get("title"), entity.get("slug")):
            return entity
    return None


def select_entity_from_cluster_list(cluster_list, identifier):
    # parsing id, which should be in parentheses after the project title
    id = re.search("(?<=\\()[^)]*(?=\\))", identifier)
    if id:
        identifier = id.group(0)
    for entity in cluster_list:
        if (hasattr(entity, "slug") and identifier is entity.slug) or (identifier in (entity.id, entity.name)):
            return entity
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


def download_manifest(deck: dict, access_token: str, environment_index: int = 0):
    try:
        environment_id = deck["environment"][environment_index]["id"]
        console.info("Requesting manifests. This process may takes a few seconds.")
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

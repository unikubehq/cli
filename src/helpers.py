import re
import sys
from urllib.parse import urljoin

import click_spinner
import requests
from requests import Session

from src import settings


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
        r = session.get(manifest_url)
    r.raise_for_status()

    manifest = r.json()
    return manifest

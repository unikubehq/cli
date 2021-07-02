import re
import sys
from urllib.parse import urljoin

import click_spinner
import requests
from requests import Session

import src.cli.console as console
from src import settings


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
    if similar_entities:
        console.warning(
            f"Entity {similar_entities[0].get('title')} has a duplicate title or slug. Specify ID directly "
            f"after title or slug in parentheses."
        )
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
        if (hasattr(entity, "slug") and identifier == entity.slug) or (identifier == entity.name):
            similar_entities.append(entity)
    if similar_entities:
        console.warning(
            f"Entity {similar_entities[0].name} has a duplicate title or slug. Specify ID directly "
            f"after title or slug in parentheses."
        )
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

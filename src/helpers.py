import sys
from urllib.parse import urljoin

import click_spinner
import requests
from requests import HTTPError, Session

from src import settings
from src.cli import console


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


def download_manifest(deck, access_token):
    try:
        environment_id = deck["environment"][0]["id"]
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
            console.error("Could not load manifest: " + str(e))
            exit(1)

    return manifest

from urllib.parse import urljoin

import click_spinner
import requests
from requests import Session

from src import settings


def get_requests_session(access_token) -> Session:
    session = requests.Session()
    session.headers.update({"Content-type": "application/json", "Authorization": "Bearer " + str(access_token)})
    return session


def download_specs(access_token: str, environment_id: str):
    session = get_requests_session(access_token=access_token)

    manifest_url = urljoin(settings.MANIFEST_DEFAULT_HOST, environment_id)
    with click_spinner.spinner():
        r = session.get(manifest_url)
    r.raise_for_status()

    manifest = r.json()
    return manifest

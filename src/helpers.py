from urllib.parse import urljoin

import requests
from requests import Session

from src import settings


def get_requests_session(access_token) -> Session:
    session = requests.Session()
    session.headers.update({"Content-type": "application/json", "Authorization": "Bearer " + str(access_token)})
    return session


def download_specs(access_token: str, cluster_level_id: str):
    session = get_requests_session(access_token=access_token)

    manifest_url = urljoin(settings.MANIFEST_DEFAULT_HOST, cluster_level_id)

    r = session.get(manifest_url)
    if r.status_code != 200:
        raise Exception(f"Access to manifest service failed (status {r.status_code})")

    manifest = r.json()
    return manifest

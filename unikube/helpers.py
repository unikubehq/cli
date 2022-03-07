import sys
from pathlib import Path
from urllib.parse import urljoin

import click_spinner
import pkg_resources
import requests
from requests import HTTPError, Session

import unikube.cli.console as console
from unikube import settings
from unikube.authentication.authentication import TokenAuthentication
from unikube.cache import Cache
from unikube.graphql_utils import EnvironmentType


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


def download_manifest(deck: dict, cache: Cache, environment_index: int = 0):
    try:
        environment_id = deck["environment"][environment_index]["id"]
        console.info("Requesting manifests. This process may take a few seconds.")
        manifest = download_specs(
            access_token=cache.auth.access_token,
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

            auth = TokenAuthentication(cache=cache)
            response = auth.refresh()
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


def compare_current_and_latest_versions():
    try:
        current_version = None
        try:
            path = Path(__file__).parent / "../VERSION"
            with path.open("r") as f:
                current_version = f.read()
        except (FileNotFoundError, PermissionError):
            console.debug("Could not read current version.")

        if not current_version:
            dist = pkg_resources.working_set.by_key.get("unikube")
            if dist:
                current_version = dist.version

        release = requests.get("https://api.github.com/repos/unikubehq/cli/releases/latest")
        if release.status_code == 403:
            console.info("Versions cannot be compared, as API rate limit was exceeded")
            return None
        latest_release_version = release.json()["tag_name"].replace("-", ".")
        if current_version != latest_release_version:
            console.info(
                f"You are using unikube version {current_version}; however, version {latest_release_version} is "
                f"available."
            )

        return current_version
    except pkg_resources.DistributionNotFound as e:
        console.warning(f"Version of the package could not be found: {e}")
    except Exception:
        import traceback

        console.info(f"Versions cannot be compared, because of error {traceback.format_exc()}")

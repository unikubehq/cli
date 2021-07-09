import pytest
from requests import HTTPError, Session

from src.helpers import download_manifest, download_specs, get_requests_session


def test_get_requests_session():
    access_token = ""
    assert type(access_token) is str

    session = get_requests_session(access_token=access_token)
    assert type(session) is Session


def test_download_specs():
    environment_id = "WRONG"
    access_token = ""

    with pytest.raises(HTTPError) as pytest_wrapped_e:
        _ = download_specs(access_token=access_token, environment_id=environment_id)

    assert pytest_wrapped_e.type == HTTPError


def test_download_manifest():
    deck = {
        "environment": [
            {
                "id": None,
            }
        ],
        "project": {
            "id": None,
        },
    }

    class Authentication:
        def refresh(self):
            return {"success": True, "response": {"access_token": ""}}

    access_token = ""
    authentication = Authentication()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        _ = download_manifest(deck=deck, authentication=authentication, access_token=access_token)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

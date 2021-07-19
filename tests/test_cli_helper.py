import pytest
from requests import HTTPError, Session

from src.local.providers.types import K8sProviderData
from src.helpers import (
    download_manifest,
    download_specs,
    get_requests_session,
    select_entity,
    select_entity_from_cluster_list,
    check_environment_type_local_or_exit,
    environment_type_from_string,
)


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


def test_select_entity():
    entity_list = [{"id": "random-id-1-2-3", "title": "test-select-entity", "clusterSettings": {"id": "1", "port": 0}}]
    identifier = "test-select-entity(random-id-1-2-3)"
    response = select_entity(entity_list, identifier)

    assert response == entity_list[0]


def test_select_entity_one_similar_entity():
    entity_list = [{"id": "random-id-1-2-3", "title": "test-select-entity", "clusterSettings": {"id": "1", "port": 0}}]
    identifier = "test-select-entity"
    response = select_entity(entity_list, identifier)
    assert response is entity_list[0]


def test_select_entity_duplicate_entities():
    entity_list = [
        {"id": "random-id-1-2-3", "title": "test-select-entity", "clusterSettings": {"id": "1", "port": 0}},
        {"id": "random-id-3-2-1", "title": "test-select-entity", "clusterSettings": {"id": "1", "port": 0}},
    ]
    identifier = "test-select-entity"
    response = select_entity(entity_list, identifier)
    assert response is None


def test_select_entity_from_cluster_list():
    entity_list = [K8sProviderData(id="random-id-1-2-3", name="test-select-entity")]
    identifier = "test-select-entity(random-id-1-2-3)"
    response = select_entity_from_cluster_list(entity_list, identifier)

    assert response == entity_list[0]


def test_select_entity_from_cluster_list_one_similar_entity():
    entity_list = [K8sProviderData(id="random-id-1-2-3", name="test-select-entity")]
    identifier = "test-select-entity"
    response = select_entity_from_cluster_list(entity_list, identifier)
    assert response is entity_list[0]


def test_select_entity_from_cluster_list_duplicate_entities():
    entity_list = [
        K8sProviderData(id="random-id-1-2-3", name="test-select-entity"),
        K8sProviderData(id="random-id-3-2-1", name="test-select-entity"),
    ]
    identifier = "test-select-entity"
    response = select_entity_from_cluster_list(entity_list, identifier)
    assert response is None


def test_environment_type_from_string():
    result = environment_type_from_string("")
    assert result is None


def test_check_environment_type_local_or_exit():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        deck = {"environment": {0: {"type": "REMOTE"}}}
        check_environment_type_local_or_exit(deck)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_environment_type_from_string():
    result = environment_type_from_string("")
    assert result is None


def test_check_environment_type_local_or_exit():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        deck = {"environment": {0: {"type": "REMOTE"}}}
        check_environment_type_local_or_exit(deck)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

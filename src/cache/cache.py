import os
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from src import settings
from src.authentication.types import AuthenticationData
from src.cache.base_file_cache import BaseFileCache
from src.cli import console


class Cache(BaseFileCache):
    userId: UUID = UUID("00000000-0000-0000-0000-000000000000")
    auth: AuthenticationData = AuthenticationData()

    def __init__(self, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "cache.json", **data):
        super().__init__(file_path=file_path, file_name=file_name, **data)


class UserInfo(BaseFileCache):
    email: str
    name: Optional[str]
    familyName: Optional[str]
    givenName: Optional[str]
    avatarImage: Optional[str]

    def __init__(self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "info.json", **data):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id))
        super().__init__(id=id, file_path=file_path, file_name=file_name, **data)


class UserSettings(BaseFileCache):
    auth_host: str = settings.AUTH_DEFAULT_HOST

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "settings.json", **data
    ):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id))
        super().__init__(file_path=file_path, file_name=file_name, **data)


class UserContext(BaseFileCache):
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    deck_id: Optional[str] = None

    def __init__(
        self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "context.json", **data
    ):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id), "cache")
        super().__init__(file_path=file_path, file_name=file_name, **data)


class Organization(BaseModel):
    title: str = None


class Project(BaseModel):
    title: str = None
    organization_id: UUID = None


class Deck(BaseModel):
    title: str = None
    project_id: UUID = None


class UserIDs(BaseFileCache):
    organization: Dict[UUID, Organization] = None
    project: Dict[UUID, Project] = None
    deck: Dict[UUID, Deck] = None

    def __init__(self, id: UUID, file_path: str = settings.CLI_UNIKUBE_DIRECTORY, file_name: str = "IDs.json", **data):
        file_path = os.path.join(settings.CLI_UNIKUBE_DIRECTORY, "user", str(id), "cache")
        super().__init__(file_path=file_path, file_name=file_name, **data)

    def update(self, data=None):
        if not data:
            # GraphQL
            try:
                from src.graphql import GraphQL

                cache = Cache()
                graph_ql = GraphQL(cache=cache)
                data = graph_ql.query(
                    """
                    query {
                        allOrganizations {
                            results {
                                id
                                title
                            }
                        }
                        allProjects {
                            results {
                                id
                                title
                                organization {
                                    id
                                }
                            }
                        }
                        allDecks {
                            results {
                                id
                                title
                                project {
                                    id
                                }
                            }
                        }
                    }
                    """,
                )
            except Exception as e:
                console.debug(e)
                return None

        organization = dict()
        for item in data["allOrganizations"]["results"]:
            organization[item["id"]] = Organization(title=item["title"])
        self.organization = organization

        project = dict()
        for item in data["allProjects"]["results"]:
            project[item["id"]] = Project(title=item["title"], organization_id=item["organization"]["id"])
        self.project = project

        deck = dict()
        for item in data["allDecks"]["results"]:
            deck[item["id"]] = Deck(title=item["title"], project_id=item["project"]["id"])
        self.deck = deck

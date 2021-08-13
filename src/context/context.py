import os
from abc import ABC, abstractmethod
from typing import List, Union

from src import settings
from src.cli import console
from src.context.helper import is_valid_uuid4
from src.context.types import ContextData
from src.graphql import GraphQL
from src.storage.user import LocalStorageUser, get_local_storage_user
from src.unikubefile.selector import unikube_file_selector
from src.unikubefile.unikube_file import UnikubeFile


class IContext(ABC):
    @abstractmethod
    def get(self, **kwargs) -> ContextData:
        raise NotImplementedError


class ClickOptionContext(IContext):
    def __init__(self, click_options):
        self.click_options = click_options

    def get(self, **kwargs) -> ContextData:
        def _get_and_validate_argument_id(argument_name: str):
            argument = self.click_options.get(argument_name, None)
            if argument:
                if is_valid_uuid4(argument):
                    argument_id = argument
                else:
                    raise Exception(f"Invalid {argument_name} id.")
            else:
                argument_id = None

            return argument_id

        # arguments
        organization_id = _get_and_validate_argument_id("organization")
        project_id = _get_and_validate_argument_id("project")
        deck_id = _get_and_validate_argument_id("deck")

        return ContextData(
            organization_id=organization_id,
            project_id=project_id,
            deck_id=deck_id,
        )


class UnikubeFileContext(IContext):
    def __init__(self, unikube_file: Union[UnikubeFile, None]):
        self.unikube_file = unikube_file

    def get(self, **kwargs) -> ContextData:
        # check if unikube file was loaded
        if not self.unikube_file:
            return ContextData()

        return self.unikube_file.get_context()


class LocalContext(IContext):
    def __init__(self, local_storage_user: Union[LocalStorageUser, None]):
        self.local_storage_user = local_storage_user

    def get(self, **kwargs) -> ContextData:
        if not self.local_storage_user:
            return ContextData()

        user_data = self.local_storage_user.get()
        return user_data.context


class ImplizitContext(IContext):
    """Implicit context, e.g.: user has only one organization"""

    def get(self, **kwargs) -> ContextData:
        return ContextData()


class ContextLogic:
    def __init__(self, context_order: List[IContext]):
        self.context_order = context_order

    def get(self) -> ContextData:
        context = ContextData()

        for context_object in self.context_order:
            # get context variables from current context
            context_current = context_object.get(current_context=context)

            # update context
            context_dict = context.dict()
            for key, value in context_current.dict().items():
                if context_dict[key] is None:
                    context_dict[key] = value
            context = ContextData(**context_dict)

            # check if all context variables have already been set
            if None not in context.dict().values():
                break

        return context


class Context:
    def __init__(self, auth):
        self._auth = auth

    def get(self, **kwargs) -> ContextData:
        local_storage_user = get_local_storage_user()

        context_logic = ContextLogic(
            [
                ClickOptionContext(
                    click_options={key: kwargs[key] for key in ("organization", "project", "deck") if key in kwargs}
                ),
                UnikubeFileContext(
                    unikube_file=unikube_file_selector.get(
                        path_unikube_file=os.path.join(
                            os.getcwd(),
                            "unikube.yaml",
                        )
                    )
                ),
                LocalContext(local_storage_user=local_storage_user),
                ImplizitContext(),
            ]
        )
        context = context_logic.get()

        # show context
        if settings.CLI_ALWAYS_SHOW_CONTEXT:
            console.info(f"context: {context}")

        return context

    def __graph_ql(self, query: str, query_variables: dict) -> Union[dict, None]:
        graph_ql = GraphQL(authentication=self._auth)
        result = graph_ql.query(
            query,
            query_variables=query_variables,
        )
        key = next(iter(result))
        data = result[key]
        return data

    def get_organization(self) -> dict:
        try:
            organization = self.__graph_ql(
                """
                query($id: UUID!) {
                    organization(id: $id) {
                        title
                        id
                    }
                }
                """,
                query_variables={
                    "id": self.get().organization_id,
                },
            )
            return organization
        except Exception as e:
            console.debug(e)
            console.error("Invalid organization context. Please adjust or remove the current context.", _exit=True)

    def get_project(self) -> dict:
        try:
            project = self.__graph_ql(
                """
                query($id: UUID) {
                    project(id: $id) {
                        title
                        id
                        organization {
                            title
                        }
                    }
                }
                """,
                query_variables={
                    "id": self.get().project_id,
                },
            )
            return project
        except Exception as e:
            console.debug(e)
            console.error("Invalid project context. Please adjust or remove the current context.", _exit=True)

    def get_deck(self) -> dict:
        try:
            deck = self.__graph_ql(
                """
                query($id: UUID) {
                    deck(id: $id) {
                        title
                        id
                    }
                }
                """,
                query_variables={
                    "id": self.get().deck_id,
                },
            )
            return deck
        except Exception as e:
            console.debug(e)
            console.error("Invalid deck context. Please adjust or remove the current context.", _exit=True)

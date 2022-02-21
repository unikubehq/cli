import os
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from unikube import settings
from unikube.cli import console
from unikube.context.helper import convert_context_arguments, is_valid_uuid4
from unikube.context.types import ContextData
from unikube.storage.user import LocalStorageUser, get_local_storage_user
from unikube.unikubefile.selector import unikube_file_selector
from unikube.unikubefile.unikube_file import UnikubeFile


class ContextError(Exception):
    pass


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
                    raise ContextError(f"Invalid {argument_name} id.")
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
    def __init__(self, path_unikube_file: Union[UnikubeFile, None]):
        self.path_unikube_file = path_unikube_file

    def get(self, **kwargs) -> ContextData:
        # get unikube file
        unikube_file = unikube_file_selector.get(path_unikube_file=self.path_unikube_file)

        # check if unikube file was loaded
        if not unikube_file:
            return ContextData()

        return unikube_file.get_context()


class LocalContext(IContext):
    def __init__(self, local_storage_user: Union[LocalStorageUser, None]):
        self.local_storage_user = local_storage_user

    def get(self, **kwargs) -> ContextData:
        if not self.local_storage_user:
            return ContextData()

        user_data = self.local_storage_user.get()
        return user_data.context


class ContextLogic:
    def __init__(self, context_order: List[IContext]):
        self.context_order = context_order

    def get(self) -> ContextData:
        context = ContextData()

        for context_object in self.context_order:
            # get context variables from current context
            try:
                context_current = context_object.get(current_context=context)
            except Exception as e:
                console.debug(e)
                context_current = ContextData()

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
                UnikubeFileContext(path_unikube_file="unikube.yaml"),
                LocalContext(local_storage_user=local_storage_user),
            ]
        )
        context = context_logic.get()

        # show context
        if settings.CLI_ALWAYS_SHOW_CONTEXT:
            from unikube.cli.context import show_context

            show_context(ctx=None, context=context)

        return context

    def get_context_ids_from_arguments(
        self, organization_argument: str = None, project_argument: str = None, deck_argument: str = None
    ) -> Tuple[str, str, str]:
        # convert context argments into ids
        organization_id, project_id, deck_id = convert_context_arguments(
            auth=self._auth,
            organization_argument=organization_argument,
            project_argument=project_argument,
            deck_argument=deck_argument,
        )

        # consider context
        context = self.get(organization=organization_id, project=project_id, deck=deck_id)
        return context.organization_id, context.project_id, context.deck_id

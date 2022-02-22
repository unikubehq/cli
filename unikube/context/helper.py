from typing import Tuple
from uuid import UUID

from slugify import slugify

from unikube.cli import console
from unikube.graphql_utils import GraphQL


class ArgumentError(Exception):
    pass


class RetryError(Exception):
    pass


# uuid validation
def is_valid_uuid4(uuid: str):
    try:
        _ = UUID(uuid, version=4)
        return True
    except Exception:
        return False


# context arguments
def __select_result(argument_value: str, results: list, exception_message: str = "context") -> UUID:
    # slugify
    if slugify(argument_value) != argument_value:
        title_list = [item.title for item in results.values()]
    else:
        title_list = [slugify(item.title) for item in results.values()]

    uuid_list = list(results.keys())

    # check if name/title exists and is unique
    count = title_list.count(argument_value)
    if count == 0:
        raise ArgumentError(f"{exception_message.capitalize()} name/slug does not exist.")

    if count > 1:
        raise ArgumentError(f"{exception_message.capitalize()} name/slug is not unique.")

    # find index
    try:
        index = title_list.index(argument_value)
    except Exception:
        raise ArgumentError(f"Invalid {exception_message} name/slug.")

    # convert name/title to uuid
    return uuid_list[index]


@retry(stop_max_attempt_number=2)
def convert_organization_argument_to_uuid(cache, argument_value: str) -> UUID:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return UUID(argument_value)

    try:
        user_IDs = UserIDs(id=cache.userId)
        uuid = __select_result(argument_value, user_IDs.organization, exception_message="organization")
    except Exception as e:
        user_IDs.update()
        raise RetryError(e)

    return uuid


def convert_project_argument_to_uuid(cache, argument_value: str, organization_id: UUID = None) -> UUID:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return UUID(argument_value)

    try:
        user_IDs = UserIDs(id=cache.userId)
        projects = user_IDs.project

        # filter
        if organization_id:
            organization = user_IDs.organization.get(organization_id)
            projects = {key: projects[key] for key in organization.project_ids}

        uuid = __select_result(argument_value, projects, exception_message="project")
    except Exception as e:
        user_IDs.update()
        raise RetryError(e)

    return uuid


def convert_deck_argument_to_uuid(
    cache, argument_value: str, organization_id: UUID = None, project_id: UUID = None
) -> UUID:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return argument_value

    try:
        user_IDs = UserIDs(id=cache.userId)
        decks = user_IDs.deck

        # filter
        filter_ids = []
        if organization_id and not project_id:
            organization = user_IDs.organization.get(organization_id)
            for project_id in organization.project_ids:
                project = user_IDs.project.get(project_id)
                filter_ids.append(project.deck_ids)

        elif not organization_id and project_id:
            project = user_IDs.project.get(project_id)
            filter_ids = project.deck_ids

        else:
            filter_ids = None

        if filter_ids:
            decks = {key: decks[key] for key in filter_ids}

        uuid = __select_result(argument_value, decks, exception_message="deck")
    except Exception as e:
        user_IDs.update()
        raise RetryError(e)

    return uuid


def convert_context_arguments(
    cache, organization_argument: str = None, project_argument: str = None, deck_argument: str = None
) -> Tuple[str, str, str]:
    try:
        # organization
        if organization_argument:
            organization_id = convert_organization_argument_to_uuid(cache, organization_argument)
            organization_id = str(organization_id)
        else:
            organization_id = None

        # project
        if project_argument:
            project_id = convert_project_argument_to_uuid(cache, project_argument, organization_id=organization_id)
            project_id = str(project_id)
        else:
            project_id = None

        # deck
        if deck_argument:
            deck_id = convert_deck_argument_to_uuid(
                cache, deck_argument, organization_id=organization_id, project_id=project_id
            )
            deck_id = str(deck_id)
        else:
            deck_id = None
    except Exception as e:
        console.error(e, _exit=True)

    return organization_id, project_id, deck_id

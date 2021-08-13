from uuid import UUID

from slugify import slugify

from src.graphql import GraphQL


# uuid validation
def is_valid_uuid4(uuid: str):
    try:
        _ = UUID(uuid, version=4)
        return True
    except Exception:
        return False


# context arguments
def __select_result(argument_value: str, results: list, exception_message: str = "context"):
    # slugify
    if slugify(argument_value) != argument_value:
        title_list = [item["title"] for item in results]
    else:
        title_list = [slugify(item["title"]) for item in results]

    # check if name/title exists and is unique
    count = title_list.count(argument_value)
    if count == 0:
        raise Exception(f"{exception_message.capitalize()} name/title does not exist.")

    if count > 1:
        raise Exception(f"{exception_message.capitalize()} name/title is not unique.")

    # find index
    try:
        index = title_list.index(argument_value)
    except Exception:
        raise Exception(f"Invalid {exception_message} name/title.")

    # convert name/title to uuid
    return results[index]["id"]


def convert_organization_argument_to_uuid(ctx, argument_value: str) -> str:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return argument_value

    # get available context options or use provided data (e.g. from previous query)
    graph_ql = GraphQL(authentication=ctx.auth)
    data = graph_ql.query(
        """
        query {
            allOrganizations {
                title
                id
            }
        }
        """
    )

    results = data["allOrganizations"]["results"]
    return __select_result(argument_value, results, exception_message="organization")


def convert_project_argument_to_uuid(ctx, argument_value: str, organization_id: str = None) -> str:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return argument_value

    # get available context options or use provided data (e.g. from previous query)
    graph_ql = GraphQL(authentication=ctx.auth)
    data = graph_ql.query(
        """
        query($organization_id: UUID) {
            allProjects(organizationId: $organization_id) {
                results {
                    title
                    id
                }
            }
        }
        """,
        query_variables={
            "organization_id": organization_id,
        },
    )

    results = data["allProjects"]["results"]
    return __select_result(argument_value, results, exception_message="project")


def convert_deck_argument_to_uuid(ctx, argument_value: str, organization_id: str = None, project_id: str = None) -> str:
    # uuid provided (no conversion required)
    if is_valid_uuid4(argument_value):
        return argument_value

    # get available context options or use provided data (e.g. from previous query)
    graph_ql = GraphQL(authentication=ctx.auth)
    data = graph_ql.query(
        """
        query($organization_id: UUID) {
            allDecks(organizationId: $organization_id, projectId: $project_id) {
                results {
                    title
                    id
                }
            }
        }
        """,
        query_variables={
            "organization_id": organization_id,
            "project_id": project_id,
        },
    )

    results = data["allDecks"]["results"]
    return __select_result(argument_value, results, exception_message="deck")


def convert_context_arguments(
    ctx, organization_argument: str = None, project_argument: str = None, deck_argument: str = None
):
    # organization
    if organization_argument:
        organization_id = convert_organization_argument_to_uuid(ctx, organization_argument)
    else:
        organization_id = None

    # project
    if project_argument:
        project_id = convert_project_argument_to_uuid(ctx, project_argument, organization_id=organization_id)
    else:
        project_id = None

    # deck
    if deck_argument:
        deck_id = convert_deck_argument_to_uuid(
            ctx, deck_argument, organization_id=organization_id, project_id=project_id
        )
    else:
        deck_id = None

    return organization_id, project_id, deck_id

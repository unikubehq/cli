import re
from typing import List, Union

import src.cli.console as console
from src.context.helper import convert_project_argument_to_uuid
from src.graphql import GraphQL


def project_list(
    ctx, organization_id: str = None, filter: List[str] = None, exclude: List[str] = None
) -> Union[None, str]:
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID) {
                allProjects(organizationId: $organization_id) {
                    results {
                        title
                        id
                        organization {
                            id
                            title
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": organization_id,
            },
        )
        project_list = data["allProjects"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # options
    choices = [project["title"] for project in project_list]
    identifiers = [project["id"] for project in project_list]

    # filter
    if filter:
        choices_filtered = []
        identifiers_filtered = []
        for project in project_list:
            if project["id"] in filter:
                choices_filtered.append(project["title"])
                identifiers_filtered.append(project["id"])

        choices = choices_filtered
        identifiers = identifiers_filtered

    # exclude
    if exclude:
        choices_filtered = []
        identifiers_filtered = []
        for project in project_list:
            if project["id"] in exclude:
                continue

            choices_filtered.append(project["title"])
            identifiers_filtered.append(project["id"])

        choices = choices_filtered
        identifiers = identifiers_filtered

    selection = console.list(
        message="Please select a project",
        choices=choices,
        identifiers=identifiers,
        message_no_choices="No projects available!",
    )
    if selection is None:
        return None

    # get identifier if available
    identifier_search = re.search("(?<=\\()[^)]*(?=\\))", selection)
    try:
        project_argument = identifier_search.group(0)
    except Exception:
        project_argument = selection

    project_id = convert_project_argument_to_uuid(ctx.auth, argument_value=project_argument)
    return project_id

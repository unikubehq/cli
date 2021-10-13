from typing import List, Union

import src.cli.console as console
from src.cli.console.input import get_identifier_or_pass
from src.context.helper import convert_project_argument_to_uuid
from src.graphql import GraphQL


def project_list(
    ctx, organization_id: str = None, filter: List[str] = None, excludes: List[str] = None
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

    selection = console.list(
        message="Please select a project",
        choices=[project["title"] for project in project_list],
        identifiers=[project["id"] for project in project_list],
        filter=filter,
        excludes=excludes,
        help_texts=[project["organization"]["title"] for project in project_list],
        message_no_choices="No projects available!",
    )
    if selection is None:
        return None

    # get identifier if available
    project_argument = get_identifier_or_pass(selection)

    project_id = convert_project_argument_to_uuid(
        ctx.auth, argument_value=project_argument, organization_id=organization_id
    )
    return project_id

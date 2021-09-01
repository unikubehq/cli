import re
from typing import Union

import src.cli.console as console
from src.context.helper import convert_organization_argument_to_uuid
from src.graphql import GraphQL


def organization_list(ctx) -> Union[None, str]:
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query {
                allOrganizations {
                    results {
                        id
                        title
                    }
                }
            }
            """
        )
        organization_list = data["allOrganizations"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    selection = console.list(
        message="Please select an organization",
        choices=[organization["title"] for organization in organization_list],
        identifiers=[organization["id"] for organization in organization_list],
        message_no_choices="No organizations available!",
    )
    if selection is None:
        return None

    # get identifier if available
    identifier_search = re.search("(?<=\\()[^)]*(?=\\))", selection)
    try:
        organization_argument = identifier_search.group(0)
    except Exception:
        organization_argument = selection

    organization_id = convert_organization_argument_to_uuid(ctx.auth, argument_value=organization_argument)
    return organization_id

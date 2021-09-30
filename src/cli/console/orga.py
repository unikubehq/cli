from typing import Union

import src.cli.console as console
from src.cli.console.input import get_identifier_or_pass
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
    organization_argument = get_identifier_or_pass(selection)

    organization_id = convert_organization_argument_to_uuid(ctx.auth, argument_value=organization_argument)
    return organization_id

from typing import Union

import src.cli.console as console
from src.cli.console.input import get_identifier_or_pass
from src.context.helper import convert_deck_argument_to_uuid
from src.graphql import GraphQL


def deck_list(ctx, organization_id: str = None, project_id: str = None) -> Union[None, str]:
    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query($organization_id: UUID, $project_id: UUID) {
                allDecks(organizationId: $organization_id, projectId: $project_id) {
                    results {
                        title
                        id
                        project {
                            id
                            title
                            organization {
                                id
                            }
                        }
                    }
                }
            }
            """,
            query_variables={
                "organization_id": organization_id,
                "project_id": project_id,
            },
        )
        deck_list = data["allDecks"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    selection = console.list(
        message="Please select a deck",
        choices=[deck["title"] for deck in deck_list],
        identifiers=[deck["id"] for deck in deck_list],
        help_texts=[deck["project"]["title"] for deck in deck_list],
        message_no_choices="No decks available!",
    )
    if selection is None:
        return None

    # get identifier if available
    deck_argument = get_identifier_or_pass(selection)

    deck_id = convert_deck_argument_to_uuid(
        ctx.auth, argument_value=deck_argument, organization_id=organization_id, project_id=project_id
    )
    return deck_id

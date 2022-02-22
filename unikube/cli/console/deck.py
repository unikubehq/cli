from typing import Optional
from uuid import UUID

import unikube.cli.console as console
from unikube.cli.console.input import get_identifier_or_pass
from unikube.context.helper import convert_deck_argument_to_uuid
from unikube.cache import UserIDs


def deck_list(ctx, organization_id: UUID = None, project_id: UUID = None) -> Optional[UUID]:
    user_IDs = UserIDs(id=ctx.user_id)
    if not user_IDs.deck:
        user_IDs.refresh()
        user_IDs.save()

    # filter
    if project_id or organization_id:
        deck_list = {}
        for id, deck in user_IDs.deck.items():
            deck_project_id = deck.project_id

            project = user_IDs.project.get(deck_project_id, None)
            if project:
                deck_organization_id = project.organization_id
            else:
                deck_organization_id = None

            if ((deck_organization_id == organization_id) or (organization_id is None)) and (
                (deck_project_id == project_id) or (project_id is None)
            ):
                deck_list[id] = deck
    else:
        deck_list = user_IDs.deck

    choices = []
    identifiers = []
    help_texts = []
    for id, deck in deck_list.items():
        choices.append(deck.title)
        identifiers.append(str(id))

        project = user_IDs.project.get(deck.project_id, None)
        if project:
            help_texts.append(project.title)
        else:
            help_texts.append(None)

    selection = console.list(
        message="Please select a deck",
        choices=choices,
        identifiers=identifiers,
        help_texts=help_texts,
        message_no_choices="No decks available!",
    )
    if selection is None:
        return None

    # get identifier if available
    deck_argument = get_identifier_or_pass(selection)

    deck_id = convert_deck_argument_to_uuid(
        ctx.cache, argument_value=deck_argument, organization_id=organization_id, project_id=project_id
    )
    return deck_id

from typing import Optional
from uuid import UUID

import unikube.cli.console as console
from unikube.cli.console.input import get_identifier_or_pass
from unikube.context.helper import convert_organization_argument_to_uuid
from unikube.cache import UserIDs


def organization_list(ctx) -> Optional[UUID]:
    user_IDs = UserIDs(id=ctx.user_id)
    if not user_IDs.organization:
        user_IDs.update()
        user_IDs.save()

    selection = console.list(
        message="Please select an organization",
        choices=[organization.title for _, organization in user_IDs.organization.items()],
        identifiers=user_IDs.organization.keys(),
        message_no_choices="No organizations available!",
    )
    if selection is None:
        return None

    # get identifier if available
    organization_argument = get_identifier_or_pass(selection)

    organization_id = convert_organization_argument_to_uuid(ctx.cache, argument_value=organization_argument)
    return organization_id

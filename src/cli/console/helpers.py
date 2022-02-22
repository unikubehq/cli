from typing import Optional
from uuid import UUID

from src.cache.cache import UserIDs


def organization_id_2_display_name(ctx, id: UUID = None) -> str:
    if not id:
        return "-"

    user_IDs = UserIDs(id=ctx.user_id)
    organization = user_IDs.organization.get(id, None)
    if organization:
        if organization.title:
            return f"{organization.title} ({id})"

    user_IDs.refresh()
    user_IDs.save()

    organization = user_IDs.organization.get(id, None)
    return f"{organization.title or '-'} ({id})"


def project_id_2_display_name(ctx, id: UUID = None) -> Optional[str]:
    if not id:
        return "-"

    user_IDs = UserIDs(id=ctx.user_id)
    project = user_IDs.project.get(id, None)
    if project:
        if project.title:
            return f"{project.title} ({id})"

    user_IDs.refresh()
    user_IDs.save()

    project = user_IDs.project.get(id, None)
    return f"{project.title or '-'} ({id})"


def deck_id_2_display_name(ctx, id: UUID = None) -> Optional[str]:
    if not id:
        return "-"

    user_IDs = UserIDs(id=ctx.user_id)
    deck = user_IDs.deck.get(id, None)
    if deck:
        if deck.title:
            return f"{deck.title} ({id})"

    user_IDs.refresh()
    user_IDs.save()

    deck = user_IDs.deck.get(id, None)
    return f"{deck.title or '-'} ({id})"

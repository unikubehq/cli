from typing import Optional
from uuid import UUID

from unikube.cache.cache import UserIDs


def organization_id_2_display_name(ctx, id: UUID = None) -> str:
    if not id:
        return "-"

    user_ids = UserIDs(id=ctx.user_id)
    organization = user_ids.organization.get(id, None)
    if organization:
        if organization.title:
            return f"{organization.title} ({id})"

    user_ids.refresh()
    user_ids.save()

    organization = user_ids.organization.get(id, None)
    return f"{organization.title or '-'} ({id})"


def project_id_2_display_name(ctx, id: UUID = None) -> Optional[str]:
    if not id:
        return "-"

    user_ids = UserIDs(id=ctx.user_id)
    project = user_ids.project.get(id, None)
    if project:
        if project.title:
            return f"{project.title} ({id})"

    user_ids.refresh()
    user_ids.save()

    project = user_ids.project.get(id, None)
    return f"{project.title or '-'} ({id})"


def deck_id_2_display_name(ctx, id: UUID = None) -> Optional[str]:
    if not id:
        return "-"

    user_ids = UserIDs(id=ctx.user_id)
    deck = user_ids.deck.get(id, None)
    if deck:
        if deck.title:
            return f"{deck.title} ({id})"

    user_ids.refresh()
    user_ids.save()

    deck = user_ids.deck.get(id, None)
    return f"{deck.title or '-'} ({id})"

from typing import List, Optional, Tuple
from uuid import UUID

import unikube.cli.console as console
from unikube.authentication.authentication import TokenAuthentication
from unikube.cache.cache import UserIDs
from unikube.cli.console.input import get_identifier_or_pass
from unikube.context.helper import convert_project_argument_to_uuid


def updated_projects(ctx, organization_id) -> Tuple[List[str], List[str], List[str]]:
    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache
    user_ids = UserIDs(id=ctx.user_id)
    user_ids.refresh()
    user_ids.save()

    if organization_id:
        project_list = {
            id: project for id, project in user_ids.project.items() if project.organization_id == organization_id
        }
    else:
        project_list = {id: project for id, project in user_ids.project.items()}
    identifiers = [str(p) for p in project_list.keys()]
    projects = list(map(lambda x: x.title, project_list.values()))
    help_texts = list(map(lambda x: user_ids.organization.get(str(x.organization_id)).title, project_list.values()))
    return identifiers, projects, help_texts


def project_list(
        ctx, organization_id: UUID = None, filter: List[str] = None, excludes: List[str] = None
) -> Optional[UUID]:
    user_ids = UserIDs(id=ctx.user_id)
    if not user_ids.project:
        user_ids.refresh()
        user_ids.save()

    # filter
    if organization_id:
        project_list = {
            id: project for id, project in user_ids.project.items() if project.organization_id == organization_id
        }
    else:
        project_list = user_ids.project

    choices = []
    identifiers = []
    help_texts = []
    for id, project in project_list.items():
        choices.append(project.title)
        identifiers.append(str(id))

        organization = user_ids.organization.get(project.organization_id, None)
        if organization:
            help_texts.append(organization.title)
        else:
            help_texts.append(None)

    update_func = lambda: updated_projects(ctx, organization_id)

    selection = console.list(
        message="Please select a project",
        choices=choices,
        identifiers=identifiers,
        filter=filter,
        excludes=excludes,
        help_texts=help_texts,
        message_no_choices="No projects available!",
        update_func=update_func,
    )
    if selection is None:
        return None

    # get identifier if available
    project_argument = get_identifier_or_pass(selection)

    project_id = convert_project_argument_to_uuid(
        ctx.cache, argument_value=project_argument, organization_id=organization_id
    )
    return project_id

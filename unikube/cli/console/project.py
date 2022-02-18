from typing import List, Union

import unikube.cli.console as console
from unikube.cli.console.input import get_identifier_or_pass
from unikube.context.helper import convert_project_argument_to_uuid
from unikube.cache.cache import UserIDs


def project_list(
    ctx, organization_id: str = None, filter: List[str] = None, excludes: List[str] = None
) -> Union[None, str]:
    user_IDs = UserIDs(id=ctx.user_id)
    if not user_IDs.project:
        user_IDs.update()
        user_IDs.save()

    # filter
    if organization_id:
        project_list = {
            id: project for id, project in user_IDs.project.items() if str(project.organization_id) == organization_id
        }
    else:
        project_list = user_IDs.project.values()

    choices = []
    identifiers = []
    help_texts = []
    for id, project in project_list.items():
        choices.append(project.title)
        identifiers.append(str(id))

        organization = user_IDs.organization.get(project.organization_id, None)
        if organization:
            help_texts.append(organization.title)
        else:
            help_texts.append(None)

    selection = console.list(
        message="Please select a project",
        choices=choices,
        identifiers=identifiers,
        filter=filter,
        excludes=excludes,
        help_texts=help_texts,
        message_no_choices="No projects available!",
    )
    if selection is None:
        return None

    # get identifier if available
    project_argument = get_identifier_or_pass(selection)

    project_id = convert_project_argument_to_uuid(
        ctx.cache, argument_value=project_argument, organization_id=organization_id
    )
    return project_id

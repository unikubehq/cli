import click

import src.cli.console as console
from src.context.helper import convert_context_arguments
from src.graphql import GraphQL
from src.storage.user import get_local_storage_user


def show_context(context):
    console.info("Context:")
    console.echo(f"- organization: {context.organization_id}")
    console.echo(f"- project: {context.project_id}")
    console.echo(f"- deck: {context.deck_id}")
    console.echo("")


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def set(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Set the local context. For more information please refer to :ref:`reference/overview:context management`.
    """

    organization_id, project_id, deck_id = convert_context_arguments(
        auth=ctx.auth, organization_argument=organization, project_argument=project, deck_argument=deck
    )

    if not (organization or project or deck):
        organization_id = console.organization_list(ctx=ctx)
        project_id = console.project_list(ctx=ctx, organization_id=organization_id)
        deck_id = console.deck_list(ctx=ctx, organization_id=organization_id, project_id=project_id)
        console.echo("")

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()

    if organization_id:
        # set organization
        user_data.context.deck_id = None
        user_data.context.project_id = None
        user_data.context.organization_id = organization_id
        local_storage_user.set(user_data)

    if project_id:
        if not organization_id:
            try:
                graph_ql = GraphQL(authentication=ctx.auth)
                data = graph_ql.query(
                    """
                    query($id: UUID) {
                        project(id: $id) {
                            organization {
                                id
                            }
                        }
                    }
                    """,
                    query_variables={
                        "id": project_id,
                    },
                )
                organization_id = data["project"]["organization"]["id"]
            except Exception as e:
                console.debug(e)
                console.exit_generic_error()

        # set project
        user_data.context.deck_id = None
        user_data.context.project_id = project_id
        user_data.context.organization_id = organization_id
        local_storage_user.set(user_data)

    if deck_id:
        if not organization_id or not project_id:
            try:
                graph_ql = GraphQL(authentication=ctx.auth)
                data = graph_ql.query(
                    """
                    query($id: UUID) {
                        deck(id: $id) {
                            project {
                                id
                                organization {
                                    id
                                }
                            }
                        }
                    }
                    """,
                    query_variables={
                        "id": deck_id,
                    },
                )
                organization_id = data["deck"]["project"]["organization"]["id"]
                project_id = data["deck"]["project"]["id"]
            except Exception as e:
                console.debug(e)
                console.exit_generic_error()

        # set deck
        user_data.context.deck_id = deck_id
        user_data.context.project_id = project_id
        user_data.context.organization_id = organization_id
        local_storage_user.set(user_data)

    show_context(user_data.context)


@click.command()
@click.option("--organization", "-o", is_flag=True, default=False, help="Remove organization context")
@click.option("--project", "-p", is_flag=True, default=False, help="Remove project context")
@click.option("--deck", "-d", is_flag=True, default=False, help="Remove deck context")
@click.pass_obj
def remove(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Remove the local context.
    """

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()

    if organization:
        user_data.context.deck_id = None
        user_data.context.project_id = None
        user_data.context.organization_id = None
        local_storage_user.set(user_data)
        console.success("Organization context removed.", _exit=True)

    if project:
        user_data.context.deck_id = None
        user_data.context.project_id = None
        local_storage_user.set(user_data)
        console.success("Project context removed.", _exit=True)

    if deck:
        user_data.context.deck_id = None
        local_storage_user.set(user_data)
        console.success("Deck context removed.", _exit=True)

    # remove complete context
    user_data.context.deck_id = None
    user_data.context.project_id = None
    user_data.context.organization_id = None
    local_storage_user.set(user_data)
    console.success("Context removed.", _exit=True)


@click.command()
@click.pass_obj
def show(ctx, **kwargs):
    """
    Show the local context.
    """

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()

    show_context(user_data.context)

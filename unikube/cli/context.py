import click

import unikube.cli.console as console
from unikube.cache import UserContext
from unikube.cli.console.helpers import (
    deck_id_2_display_name,
    organization_id_2_display_name,
    project_id_2_display_name,
)
from unikube.context.helper import convert_context_arguments
from unikube.graphql_utils import GraphQL


def show_context(ctx, context):
    organization = organization_id_2_display_name(ctx=ctx, id=context.organization_id)
    project = project_id_2_display_name(ctx=ctx, id=context.project_id)
    deck = deck_id_2_display_name(ctx=ctx, id=context.deck_id)

    console.info("Context:")
    console.echo(f"- organization: {organization}")
    console.echo(f"- project: {project}")
    console.echo(f"- deck: {deck}")
    console.echo("")


@click.command()
@click.option("--organization", "-o", help="Select an organization")
@click.option("--project", "-p", help="Select a project")
@click.option("--deck", "-d", help="Select a deck")
@click.pass_obj
def set(ctx, organization=None, project=None, deck=None, **kwargs):
    """
    Set the local context.
    """

    organization_id, project_id, deck_id = convert_context_arguments(
        cache=ctx.cache, organization_argument=organization, project_argument=project, deck_argument=deck
    )

    if not (organization or project or deck):
        organization_id = console.organization_list(ctx=ctx)
        project_id = console.project_list(ctx=ctx, organization_id=organization_id)
        deck_id = console.deck_list(ctx=ctx, organization_id=organization_id, project_id=project_id)
        console.echo("")

    # user_data / context
    user_context = UserContext(id=ctx.user_id)

    if organization_id:
        # set organization
        user_context.deck_id = None
        user_context.project_id = None
        user_context.organization_id = organization_id
        user_context.save()

    if project_id:
        if not organization_id:
            try:
                graph_ql = GraphQL(cache=ctx.cache)
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
        user_context.deck_id = None
        user_context.project_id = project_id
        user_context.organization_id = organization_id
        user_context.save()

    if deck_id:
        if not organization_id or not project_id:
            try:
                graph_ql = GraphQL(cache=ctx.cache)
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
        user_context.deck_id = deck_id
        user_context.project_id = project_id
        user_context.organization_id = organization_id
        user_context.save()

    show_context(ctx=ctx, context=user_context)


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
    user_context = UserContext(id=ctx.user_id)

    if organization:
        user_context.deck_id = None
        user_context.project_id = None
        user_context.organization_id = None
        user_context.save()
        console.success("Organization context removed.", _exit=True)

    if project:
        user_context.deck_id = None
        user_context.project_id = None
        user_context.save()
        console.success("Project context removed.", _exit=True)

    if deck:
        user_context.deck_id = None
        user_context.save()
        console.success("Deck context removed.", _exit=True)

    # remove complete context
    user_context.deck_id = None
    user_context.project_id = None
    user_context.organization_id = None
    user_context.save()
    console.success("Context removed.", _exit=True)


@click.command()
@click.pass_obj
def show(ctx, **kwargs):
    """
    Show the context.
    """

    # user_data / context
    user_context = UserContext(id=ctx.user_id)
    show_context(ctx=ctx, context=user_context)

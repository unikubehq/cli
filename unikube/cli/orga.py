import click

import unikube.cli.console as console
from unikube.authentication.authentication import TokenAuthentication
from unikube.graphql_utils import GraphQL


@click.command()
@click.pass_obj
def list(ctx, **kwargs):
    """
    List all your organizations.
    """

    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query {
                allOrganizations {
                    results {
                        title
                        id
                        description
                    }
                }
            }
            """
        )
        organization_list = data["allOrganizations"]["results"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # console
    if len(organization_list) < 1:
        console.info(
            "No organization available. Please go to https://app.unikube.io and create an organization.", _exit=True
        )

    console.table(
        data={
            "id": [item["id"] for item in organization_list],
            "title": [item["title"] for item in organization_list],
            "description": [item["description"] for item in organization_list],
        },
        headers=["id", "name", "description"],
    )


@click.command()
@click.argument("organization", required=False)
@click.pass_obj
def info(ctx, organization, **kwargs):
    """
    Display further information of the selected organization.
    """

    auth = TokenAuthentication(cache=ctx.cache)
    _ = auth.refresh()
    ctx.cache = auth.cache

    # context
    organization_id, _, _ = ctx.context.get_context_ids_from_arguments(organization_argument=organization)

    # argument
    if not organization_id:
        organization_id = console.organization_list(ctx)
        if not organization_id:
            return None

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query($id: UUID!) {
                organization(id: $id) {
                    id
                    title
                    description
                }
            }
            """,
            query_variables={"id": str(organization_id)},
        )
        organization_selected = data["organization"]
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # console
    if organization_selected:
        console.table(
            data={
                "key": [k for k in organization_selected.keys()],
                "value": [v for v in organization_selected.values()],
            },
            headers=["Key", "Value"],
        )
    else:
        console.error("Organization does not exist.")

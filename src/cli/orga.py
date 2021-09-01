import click

import src.cli.console as console
from src.graphql import GraphQL
from src.keycloak.permissions import KeycloakPermissions


@click.command()
@click.pass_obj
def list(ctx, **kwargs):
    """
    List all your organizations.
    """

    context = ctx.context.get()

    # keycloak
    try:
        keycloak_permissions = KeycloakPermissions(authentication=ctx.auth)
        permission_list = keycloak_permissions.get_permissions_by_scope("organization:*")
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # append "(active)"
    if context.organization_id:
        for permission in permission_list:
            if permission.rsid == context.organization_id:
                permission.rsid += " (active)"

    # console
    organization_list = [
        {
            "id": permission.rsid,
            "name": permission.rsname.replace("organization ", ""),
        }
        for permission in permission_list
    ]
    console.table(
        data=organization_list,
        headers={
            "id": "id",
            "name": "name",
        },
    )


@click.command()
@click.argument("organization", required=False)
@click.pass_obj
def info(ctx, organization, **kwargs):
    """
    Display further information of the selected organization.
    """

    # context
    organization_id, _, _ = ctx.context.get_context_ids_from_arguments(organization_argument=organization)

    # argument
    if not organization_id:
        organization_id = console.organization_list(ctx)
        if not organization_id:
            return None

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
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
            query_variables={"id": organization_id},
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

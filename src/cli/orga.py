import click

import src.cli.console as console
from src.graphql import GraphQL
from src.helpers import select_entity
from src.keycloak.permissions import KeycloakPermissions
from src.storage.user import get_local_storage_user


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
        permission_list = None
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

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            {
                allOrganizations {
                    results {
                        id
                        title
                        description
                    }
                }
            }
            """
        )
    except Exception as e:
        data = None
        console.debug(e)
        console.exit_generic_error()

    organization_list = data["allOrganizations"]["results"]

    # argument
    if not organization:
        # argument from context
        context = ctx.context.get()
        if context.organization_id:
            organization_instance = ctx.context.get_organization()
            organization = organization_instance["title"] + f"({organization_instance['id']})"

        # argument from console
        else:
            organization = console.list(
                message="Please select an organization",
                choices=[organization["title"] + f"({organization['id']})" for organization in organization_list],
            )
            if organization is None:
                return None

    # select
    organization_selected = select_entity(organization_list, organization)

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

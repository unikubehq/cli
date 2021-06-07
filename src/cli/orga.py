import click

import src.cli.console as console
from src.graphql import GraphQL
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
@click.argument("organization_title", required=False)
@click.pass_obj
def info(ctx, organization_title, **kwargs):
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
    if not organization_title:
        # argument from context
        context = ctx.context.get()
        if context.organization_id:
            organization = ctx.context.get_organization()
            organization_title = organization["title"]

        # argument from console
        else:
            organization_title = console.list(
                message="Please select an organization",
                choices=[organization["title"] for organization in organization_list],
            )
            if organization_title is None:
                return None

    # select
    organization_selected = None
    for organization in organization_list:
        if organization["title"] == organization_title:
            organization_selected = organization
            break

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


@click.command()
@click.argument("organization_id", required=False)
@click.option("--remove", "-r", is_flag=True, default=False, help="Remove local organization context")
@click.pass_obj
def use(ctx, organization_id, remove, **kwargs):
    """
    Set local organization context.
    """

    # user_data / context
    local_storage_user = get_local_storage_user()
    user_data = local_storage_user.get()

    # option: --remove
    if remove:
        user_data.context.deck_id = None
        user_data.context.project_id = None
        user_data.context.organization_id = None
        local_storage_user.set(user_data)
        console.success("Organization context removed.")
        return None

    # GraphQL
    try:
        graph_ql = GraphQL(authentication=ctx.auth)
        data = graph_ql.query(
            """
            query {
                allOrganizations {
                    results {
                        id
                        title
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
    organization_dict = {organization["id"]: organization["title"] for organization in organization_list}

    # argument
    if not organization_id:
        organization_title = console.list(
            message="Please select an organization",
            choices=organization_dict.values(),
        )
        if organization_title is None:
            return False

        for id, title in organization_dict.items():
            if title == organization_title:
                organization_id = id

    # set organization
    user_data.context.deck_id = None
    user_data.context.project_id = None
    user_data.context.organization_id = organization_id
    local_storage_user.set(user_data)

    console.success(f"Organization context: {user_data.context}")

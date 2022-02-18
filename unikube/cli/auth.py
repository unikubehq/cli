from getpass import getpass

import click

import unikube.cli.console as console
from unikube.helpers import compare_current_and_latest_versions
from unikube.authentication.flow import password_flow, web_flow
from unikube.graphql_utils import GraphQL
from unikube.authentication.authentication import TokenAuthentication
from unikube.cache import UserIDs, UserInfo


@click.command()
@click.option("--email", "-e", type=str, help="Authentication email")
@click.option("--password", "-p", type=str, help="Authentication password")
@click.pass_obj
def login(ctx, email, password, **kwargs):
    """
    Authenticate with a Unikube host. The default login process is a Browser-based method.
    If you want to login without being redirected to the Browser, you can just specify the parameter
    ``-e`` for email and enable the direct login method. For a non-interactive login, you can provide
    ``-p`` along with the password.
    """

    compare_current_and_latest_versions()

    # select login flow
    if email or password:
        if not email:
            email = click.prompt("email", type=str)
        if not password:
            password = getpass("password:")

        success = password_flow(ctx, email, password)
    else:
        success = web_flow(ctx)

    # error
    if not success:
        console.error("Login failed. Please check email and password.", _exit=True)

    # GraphQL
    try:
        graph_ql = GraphQL(cache=ctx.cache)
        data = graph_ql.query(
            """
            query {
                user {
                    id
                    email
                    name
                    familyName
                    givenName
                    avatarImage
                }
                allOrganizations {
                    results {
                        id
                        title
                    }
                }
                allProjects {
                    results {
                        id
                        title
                        organization {
                            id
                        }
                    }
                }
                allDecks {
                    results {
                        id
                        title
                        project {
                            id
                        }
                    }
                }
            }
            """,
        )

        user = data.get("user", None)
    except Exception as e:
        console.debug(e)
        console.exit_generic_error()

    # cache user_id
    try:
        ctx.cache.userId = user["id"]
        ctx.cache.save()
    except Exception as e:
        console.debug(e)

    # cache user information
    try:
        user_info = UserInfo(**user)
        user_info.save()
    except Exception as e:
        console.debug(e)

    # cache IDs
    try:
        user_IDs = UserIDs(id=user["id"])
        user_IDs.update(data)
        user_IDs.save()
    except Exception as e:
        console.debug(e)

    console.success("Login successful.")
    return True


@click.command()
@click.pass_obj
def logout(ctx, **kwargs):
    """
    Log out of a Unikube host.
    """

    auth = TokenAuthentication(cache=ctx.cache)
    auth.logout()

    console.info("Logout completed.")
    return True


@click.command()
@click.option("--token", "-t", is_flag=True, default=False, help="Show token information.")
@click.pass_obj
def status(ctx, token=False, **kwargs):
    """
    View authentication status.
    """

    # show token information
    if token:
        console.info(f"access token: {ctx.cache.auth.access_token}")
        console.echo("---")
        console.info(f"refresh token: {ctx.cache.auth.refresh_token}")
        console.echo("---")
        console.info(f"requesting party token: {ctx.cache.auth.requesting_party_token}")
        console.echo("")

    # verify
    auth = TokenAuthentication(cache=ctx.cache)
    response = auth.verify()

    if response["success"]:
        console.success("Authentication verified.")
    else:
        console.info("Authentication could not be verified.")

    return True

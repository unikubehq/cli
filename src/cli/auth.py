from getpass import getpass

import click
import jwt

import src.cli.console as console
from src import settings


@click.command()
@click.option("--email", "-e", type=str, help="Authentication email")
@click.option("--password", "-p", type=str, help="Authentication password")
@click.pass_obj
def login(ctx, email, password, **kwargs):
    """
    Authenticate with a Unikube host.
    """

    # email
    if not email:
        email = click.prompt("email", type=str)

    # password
    if not password:
        password = getpass("password:")

    response = ctx.auth.login(
        email,
        password,
    )
    if response["success"]:
        try:
            token = jwt.decode(
                response["response"]["access_token"],
                algorithms=["RS256"],
                audience=settings.TOKEN_AUDIENCE,
                options={"verify_signature": False},
            )
        except Exception as e:
            console.debug(e)
            console.debug(response)
            console.error("Login failed. Your token does not match.")
            return False

        if token["given_name"]:
            console.success(f'Login success. Hello {token["given_name"]}!')
        else:
            console.success("Login success.")

    else:
        console.error("Login failed. Please check your e-mail or re-enter your password.")

    return True


@click.command()
@click.pass_obj
def logout(ctx, **kwargs):
    """
    Log out of a Unikube host.
    """

    ctx.auth.logout()
    console.info("Logout completed.")

    return True


@click.command()
@click.pass_obj
def status(ctx, **kwargs):
    """
    View authentication status.
    """

    response = ctx.auth.verify()
    if response["success"]:
        console.success("Authentication verified.")
    else:
        console.info("Authentication could not be verified.")

    return True

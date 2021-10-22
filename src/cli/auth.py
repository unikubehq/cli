from getpass import getpass

import click

import src.cli.console as console
from src.authentication.flows import password_flow, web_flow
from src.helpers import compare_current_and_latest_versions


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
    if email or password:
        if not email:
            email = click.prompt("email", type=str)
        if not password:
            password = getpass("password:")
        return password_flow(ctx, email, password)
    return web_flow(ctx)


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

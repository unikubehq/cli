from getpass import getpass

import click
from oic import rndstr
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

import src.cli.console as console
from src import settings
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


def password_flow(ctx, email, password):
    response = ctx.auth.login(
        email,
        password,
    )
    if response["success"]:
        try:
            token = ctx.auth.token_from_response(response)
        except Exception as e:
            console.debug(e)
            console.debug(response)
            console.error("Login failed. Your token does not match.")
            return False

        if token["given_name"]:
            console.success(f'Login successful. Hello {token["given_name"]}!')
        else:
            console.success("Login successful.")
    else:
        console.error("Login failed. Please check email and password.")
    return True


def web_flow(ctx):
    client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
    issuer = f"{settings.AUTH_DEFAULT_HOST}/auth/realms/unikube"
    client.provider_config(issuer)

    state = rndstr()
    nonce = rndstr()

    # 1. run callback server
    from src.authentication.web import run_callback_server

    port = run_callback_server(state, nonce, client, ctx)

    # 2. send to login with redirect url.
    args = {
        "client_id": "cli",
        "response_type": ["token"],
        "response_mode": "form_post",
        "scope": ["openid"],
        "nonce": nonce,
        "state": state,
        "redirect_uri": f"http://localhost:{port}",
    }

    auth_req = client.construct_AuthorizationRequest(request_args=args)
    login_url = auth_req.request(client.authorization_endpoint)
    console.info("If your Browser does not open automatically, go to the following URL and login:")
    console.link(login_url)
    click.launch(login_url)
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

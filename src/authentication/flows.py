import click
from oic import rndstr
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

import src.cli.console as console
from src import settings


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
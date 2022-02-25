import click
from oic import rndstr
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

import unikube.cli.console as console
from unikube import settings
from unikube.authentication.authentication import TokenAuthentication
from unikube.cache import Cache
from unikube.cache.cache import UserIDs, UserInfo, UserSettings
from unikube.graphql_utils import GraphQL


def cache_information(cache: Cache):
    # GraphQL
    try:
        graph_ql = GraphQL(cache=cache)
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
        cache.userId = user["id"]
        cache.save()
    except Exception as e:
        console.debug(e)

    # cache user settings
    try:
        user_settings = UserSettings(id=user["id"])
        user_settings.save()
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
        user_ids = UserIDs(id=user["id"])
        user_ids.update(data)
        user_ids.save()
    except Exception as e:
        console.debug(e)


def password_flow(ctx, email: str, password: str) -> bool:
    auth = TokenAuthentication(cache=ctx.cache)
    response = auth.login(
        email,
        password,
    )
    if not response["success"]:
        return False

    try:
        _ = auth.token_from_response(response)
    except Exception as e:
        console.debug(e)
        console.debug(response)
        return False

    cache_information(cache=ctx.cache)

    return True


def web_flow(ctx) -> bool:
    client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
    issuer = f"{settings.AUTH_DEFAULT_HOST}/auth/realms/unikube"
    client.provider_config(issuer)

    state = rndstr()
    nonce = rndstr()

    # 1. run callback server
    from unikube.authentication.web import run_callback_server

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

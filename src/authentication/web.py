import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from socket import AF_INET, SOCK_STREAM, gethostbyname, socket
from threading import Thread
from urllib.parse import parse_qs

from oic.oic import AccessTokenResponse, AuthorizationResponse, Client

from src.authentication.types import AuthenticationData
from src.cli import console
from src.context import ClickContext

CALLBACK_PORT_RANGE = range(44444, 44448)


def get_callback_port() -> int:
    t_IP = gethostbyname("localhost")
    for port in CALLBACK_PORT_RANGE:
        conn = (s := socket(AF_INET, SOCK_STREAM)).connect_ex((t_IP, port))
        s.close()
        if conn:
            break
    else:
        raise Exception("No port in the range 44444-44447 is available.")
    return port


def run_callback_server(state: str, nonce: str, client: Client, ctx: ClickContext) -> int:
    class CallbackHandler(BaseHTTPRequestHandler):
        """
        This handles the redirect from the Keycloak after the web login.
        A simple http server is started when the user is sent to the keycloak
        web frontend to authenticate.
        """

        def get_post_data(self) -> dict:
            post_body = self.rfile.read(int(self.headers.get("content-length", 0)))
            return {k.decode(): v[0].decode() for k, v in parse_qs(post_body).items()}

        def send_text_response(self, response_body):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def do_POST(self):
            POST = self.get_post_data()

            if POST["state"] != state:
                raise Exception(f"Invalid state: {POST['state']}")

            response = ctx.auth._get_requesting_party_token(POST["access_token"])

            login_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "login.html"))
            text = login_file.read()
            login_file.close()

            # select response
            if not response["success"]:
                console.error("Login failed!")
                text = (
                    "Login failed! Could not retrieve requesting party token. "
                    "Please try again or contact your System administrator"
                )
            else:
                try:
                    token = ctx.auth.token_from_response(response)
                except Exception as e:
                    console.debug(e)
                    console.debug(response)
                    console.error("Login failed!")
                    text = "Login failed! Your token does not match."
                else:
                    ctx.auth.general_data.authentication = AuthenticationData(
                        email=token["email"],
                        access_token=response["response"]["access_token"],
                        refresh_token=response["response"]["refresh_token"],
                        requesting_party_token=True,
                    )
                    ctx.auth.local_storage_general.set(ctx.auth.general_data)

                    if given_name := token.get("given_name", ""):
                        greeting = f"Hello {given_name}!"
                    else:
                        greeting = "Hello!"

                    html_close = "<a href='javascript:window.close();'>close</a>"

                    text_html = (
                        f"You have successfully logged in. You can {html_close} this browser tab and return "
                        f"to the shell."
                    )

                    text_plain = (
                        "You have successfully logged in. You can close this browser tab and return to the shell."
                    )

                    greeting_text = "{greeting} {text}".format(greeting=greeting, text=text_plain)

                    greeting_html = "{greeting} {text}".format(greeting=greeting, text=text_html)

                    text = text.replace("##text_placeholder##", greeting_html)
                    text = text.replace("##headline##", "Login Successful")
                    console.success(f"{greeting_text} You are now logged in!")
            response_body = text.encode("utf-8")
            self.send_text_response(response_body)
            Thread(target=server.shutdown).start()

        def log_request(self, *args, **kwargs):
            return

    port = get_callback_port()
    server = HTTPServer(("", port), CallbackHandler)
    Thread(target=server.serve_forever).start()
    return port

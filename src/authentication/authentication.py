from urllib.parse import urljoin

import jwt
import requests

import src.cli.console as console
from src import settings
from src.authentication.types import AuthenticationData
from src.storage.general import LocalStorageGeneral
from src.storage.user import LocalStorageUser


class IAuthentication:
    def check(self):
        raise NotImplementedError

    def login(self, email: str, password: str) -> dict:
        raise NotImplementedError

    def logout(self):
        raise NotImplementedError

    def verify(self) -> dict:
        raise NotImplementedError

    def refresh(self) -> dict:
        raise NotImplementedError

    def verify_or_refresh(self) -> bool:
        raise NotImplementedError


class TokenAuthentication(IAuthentication):
    def __init__(
        self,
        local_storage_general: LocalStorageGeneral,
        timeout=settings.TOKEN_TIMEOUT,
    ):
        self.local_storage_general = local_storage_general

        self.general_data = self.local_storage_general.get()
        self.timeout = timeout

        self.url_public_key = urljoin(self.__get_host(), settings.TOKEN_PUBLIC_KEY)
        self.url_login = urljoin(self.__get_host(), settings.TOKEN_LOGIN_PATH)
        self.url_verify = urljoin(self.__get_host(), settings.TOKEN_VERIFY_PATH)
        self.url_refresh = urljoin(self.__get_host(), settings.TOKEN_REFRESH_PATH)

        self.client_id = settings.KC_CLIENT_ID

        # RPT
        self.requesting_party_token_audience = settings.TOKEN_RPT_AUDIENCE

    def __get_host(self) -> str:
        try:
            local_storage_user = LocalStorageUser(user_email=self.general_data.authentication.email)
            user_data = local_storage_user.get()
            auth_host = user_data.config.auth_host

            if not auth_host:
                raise Exception("User data config does not specify an authentication host.")

            return auth_host

        except Exception:
            return settings.AUTH_DEFAULT_HOST

    def _get_requesting_party_token(self, access_token):
        # requesting party token (RPT)
        response = self.__request(
            url=self.url_login,
            data={
                "audience": self.requesting_party_token_audience,
                "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            },
            headers={"Authorization": f"Bearer {access_token}"},
            message_exception="Could not establish a server connection.",
            message_200="",
            message_400="Wrong user credentials or account does not exist.",
            message_500="There was an server error.",
        )

        # select response
        if not response["success"]:
            return response

        return response

    def check(self):
        # login required
        if not self.verify_or_refresh():
            console.exit_login_required()

    def login(
        self,
        email: str,
        password: str,
    ) -> dict:
        # set/update user config
        local_storage_user = LocalStorageUser(user_email=email)
        user_data = local_storage_user.get()
        user_data.config.auth_host = settings.AUTH_DEFAULT_HOST
        local_storage_user.set(user_data)

        # access token + refresh token
        response_token = self.__request(
            url=self.url_login,
            data={
                "username": email,
                "password": password,
                "grant_type": "password",
                "client_id": self.client_id,
            },
            message_exception="Could not establish a server connection.",
            message_200="",
            message_400="Wrong user credentials or account does not exist.",
            message_500="There was an server error.",
        )

        if not response_token["success"]:
            return response_token

        # requesting party token (RPT)
        response_RPT = self._get_requesting_party_token(response_token["response"]["access_token"])

        # select response
        if response_RPT["success"]:
            response = response_RPT
            requesting_party_token = True
        else:
            response = response_token
            requesting_party_token = False

        # set authentication data
        self.general_data.authentication = AuthenticationData(
            email=email,
            access_token=response["response"]["access_token"],
            refresh_token=response["response"]["refresh_token"],
            requesting_party_token=requesting_party_token,
        )

        self.local_storage_general.set(self.general_data)

        return response

    def logout(self):
        self.general_data.authentication = AuthenticationData()
        self.local_storage_general.set(self.general_data)

    def verify(self) -> dict:
        # keycloak
        access_token = self.general_data.authentication.access_token
        response = self.__request(
            url=self.url_verify,
            data={},
            headers={"Authorization": f"Bearer {access_token}"},
            message_exception="Could not establish a server connection.",
            message_200="",
            message_400="Invalid or expired login data, please log in again with 'unikube login'.",
            message_500="There was an server error.",
        )
        return response

    def refresh(self) -> dict:
        # request
        refresh_token = self.general_data.authentication.refresh_token
        response_token = self.__request(
            url=self.url_refresh,
            data={
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "client_id": self.client_id,
            },
            message_exception="Could not establish a server connection.",
            message_200="",
            message_400="Refresh token expired or account does not exist.",
            message_500="There was an server error.",
        )

        if not response_token["success"]:
            return response_token

        # requesting party token (RPT)
        response_RPT = self._get_requesting_party_token(response_token["response"]["access_token"])

        # select response
        if response_RPT["success"]:
            response = response_RPT
            requesting_party_token = True
        else:
            response = response_token
            requesting_party_token = False

        # update token
        if response["success"]:
            self.general_data = self.local_storage_general.get()
            self.general_data.authentication.access_token = response["response"]["access_token"]
            self.general_data.authentication.refresh_token = response["response"]["refresh_token"]
            self.general_data.authentication.requesting_party_token = requesting_party_token
            self.local_storage_general.set(self.general_data)

        return response

    def verify_or_refresh(self) -> bool:
        # verify
        response = self.verify()
        if response["success"]:
            return True

        # refresh
        response = self.refresh()
        if response["success"]:
            return True

        # exception messsage
        console.debug(response["message"])

        return False

    def __request(
        self,
        url,
        data,
        message_exception,
        message_200,
        message_400,
        message_500,
        headers=None,
    ) -> dict:
        # request
        try:
            req = requests.post(
                url,
                data,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as e:
            console.debug(e)
            return {
                "success": False,
                "message": message_exception,
                "response": None,
            }

        # return
        if req.status_code == 200:
            success = True
            message = message_200

        elif req.status_code in [400, 401, 404]:
            success = False
            message = message_400

        elif req.status_code in [500, 501, 502, 503]:
            success = False
            message = message_500

        else:
            success = False
            message = ""

        # get json response
        try:
            response = req.json()
        except Exception:
            response = None

        return {
            "success": success,
            "message": message,
            "response": response,
        }

    def token_from_response(self, response):
        token = jwt.decode(
            response["response"]["access_token"],
            algorithms=["RS256"],
            audience=settings.TOKEN_AUDIENCE,
            options={"verify_signature": False},
        )
        return token


def get_authentication():
    token_authentication = TokenAuthentication(local_storage_general=LocalStorageGeneral())
    return token_authentication

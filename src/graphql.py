from enum import Enum
from typing import Union

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from retrying import retry

import src.cli.console as console
from src import settings


# EnvironmentType
class EnvironmentType(Enum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class RetryException(Exception):
    pass


# retry exception logic
def retry_exception(exception):
    return isinstance(exception, RetryException)


class GraphQL:
    def __init__(
        self,
        authentication,
        url=settings.GRAPHQL_URL,
        timeout=settings.GRAPHQL_TIMEOUT,
    ):
        self.url = url
        self.timeout = timeout

        # automatic token refresh
        self.authentication = authentication
        self.access_token = str(authentication.general_data.authentication.access_token)

        # client
        self.client = self._client()

    def _client(self):
        # header
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + str(self.access_token),
        }

        # transport
        transport = RequestsHTTPTransport(
            url=self.url,
            use_json=True,
            headers=headers,
            verify=False,
            retries=3,
            timeout=self.timeout,
        )

        # client
        client = Client(transport=transport)

        return client

    @retry(retry_on_exception=retry_exception, stop_max_attempt_number=2)
    def query(
        self,
        query: str,
        query_variables: dict = None,
    ) -> Union[dict, None]:
        try:
            query = gql(query)
            data = self.client.execute(
                document=query,
                variable_values=query_variables,
            )

        except requests.exceptions.HTTPError:
            # refresh token
            response = self.authentication.refresh()
            if not response["success"]:
                console.exit_login_required()

            self.access_token = response["response"]["access_token"]
            self.client = self._client()

            raise RetryException("retry")

        return data

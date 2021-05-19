import fnmatch
import uuid
from functools import lru_cache
from typing import KeysView, List, Optional, Union

import jwt
from pydantic import BaseModel
from retrying import retry

from src import settings
from src.authentication.authentication import IAuthentication
from src.authentication.types import AuthenticationData
from src.cli import console


class KeycloakPermissionData(BaseModel):
    scopes: Optional[List[str]]
    rsid: str
    rsname: str


class KeycloakPermissions:
    def __init__(self, authentication: IAuthentication):
        self.authentication = authentication

    def _permission_data(self):
        # verify
        response = self.authentication.verify_or_refresh()
        if not response:
            console.exit_login_required()

        # get authentication_data
        authentication_data = self.authentication.general_data.authentication

        # check for requesting_party_token
        if not authentication_data.requesting_party_token:
            raise Exception("Requesting Party Token (RPT) required.")

        # decode requesting_party_token
        requesting_party_token = self._decode_requesting_party_token(
            requesting_party_token=authentication_data.access_token
        )

        # convert
        permission_data = KeycloakPermissions._convert(requesting_party_token["authorization"]["permissions"])

        return permission_data

    def _decode_requesting_party_token(self, requesting_party_token: str) -> dict:
        # decode
        try:
            token = jwt.decode(
                requesting_party_token,
                algorithms=["RS256"],
                audience=settings.TOKEN_AUDIENCE,
                options={"verify_signature": False},
            )
        except Exception as e:
            console.debug(e)
            raise Exception("Requesting Party Token (RPT) could not be decoded.")

        return token

    @staticmethod
    def _convert(permissions: dict) -> List[KeycloakPermissionData]:
        keycloak_permission_list = []
        for permission_dict in permissions:
            keycloak_permission = KeycloakPermissionData(**permission_dict)
            keycloak_permission_list.append(keycloak_permission)

        return keycloak_permission_list

    @lru_cache(10)
    def get_permissions_by_scope(self, scope: str) -> List[KeycloakPermissionData]:
        """
        Return a list of resources with the given scope. Supports to filter with wildcards
        e.g. organization:*.
        """
        permission_data = self._permission_data()

        results = []
        for permission in permission_data:
            if permission.scopes:
                # 'scopes': ['organization:view', 'organization:edit']
                matched = fnmatch.filter(permission.scopes, scope)
                if matched:
                    results.append(permission)

        return results

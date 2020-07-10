import requests
import msal
from .settings import AZURE_AUTH


class GraphApi:
    SCOPE = ["https://graph.microsoft.com/.default"]
    ENDPOINT = "https://graph.microsoft.com/v1.0"

    _cache = None

    def __init__(self, user=None):
        # API services
        self.cache = msal.SerializableTokenCache()
        if self._cache:
            self.cache.deserialize(self.cache)
        self.cca = GraphApi._build_msal_app(cache=self.cache)
        self._users_api = _GraphApiUser(self.cache, self.cca)

    @property
    def token(self):
        if result := self.cca.acquire_token_silent(scopes=GraphApi.SCOPE, account=None):
            return result.get("access_token")
        result = self.cca.acquire_token_for_client(scopes=GraphApi.SCOPE)
        return result.get("access_token")

    @property
    def auth_header(self):
        return {"Authorization": "Bearer " + self.token}

    @property
    def user(self):
        return self._users_api

    def custom(self, url):
        """
        Calls a custom url using 'v1.0' endpoint and returns a json response
        :param url: The url to call.
        :return: parsed json response
        """
        return requests.get(
            f"{GraphApi.ENDPOINT}{url}", headers={**self.auth_header}
        ).json()

    def beta(self, url):
        """
        Calls a custom url using 'beta' endpoint and returns a json response
        :param url: The url to call.
        :return: parsed json response
        """
        return requests.get(
            f"https://graph.microsoft.com/beta{url}", headers={**self.auth_header}
        ).json()

    @staticmethod
    def _build_msal_app(cache=None, authority=None):
        from django.conf import settings

        config = getattr(settings, "AZURE_AUTH")

        return msal.ConfidentialClientApplication(
            config.get("CLIENT_ID"),
            authority=authority or config.get("AUTHORITY"),
            client_credential=config.get("CLIENT_SECRET"),
            token_cache=cache,
        )


class _GraphApiUser:
    def __init__(
            self,
            cache: msal.SerializableTokenCache,
            cca: msal.ConfidentialClientApplication,
    ):
        self.cache = cache
        self.cca = cca

    def get(self, email):
        return requests.get(
            f"{GraphApi.ENDPOINT}/users/{email}", headers={**self.auth_header},
        ).json()

    def list(self):
        return requests.get(
            f"{GraphApi.ENDPOINT}/users?$select=givenName,surname,jobTitle,id,"
            f"userPrincipalName",
            headers={**self.auth_header},
        ).json()

    def create(self, username: str, first_name: str, last_name: str, password: str,
               job_title: str = ''):
        if None in (username, first_name, last_name, password):
            return False

        res = requests.post(
            f"{GraphApi.ENDPOINT}/users",
            headers={**self.auth_header},
            json={
                "accountEnabled": True,
                "displayName": f"{first_name} {last_name}",
                "mailNickname": username,
                "userPrincipalName": username + '@' + AZURE_AUTH.get('DOMAIN'),
                "givenName": first_name,
                "surname": last_name,
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": False,
                    "password": password,
                },
                "jobTitle": job_title,
            },
        )
        if res.status_code == 201:
            return True
        else:
            return res.json()

    def update(self, azure_object_id, username: str, first_name: str, last_name: str,
               password: str):
        if None in (username, first_name, last_name, password):
            return False

        res = requests.patch(
            f"{GraphApi.ENDPOINT}/users/{azure_object_id}",
            headers={**self.auth_header},
            json={
                "displayName": f"{first_name} {last_name}",
                "mailNickname": username,
                "userPrincipalName": username + '@' + AZURE_AUTH.get('DOMAIN'),
                "givenName": first_name,
                "surname": last_name,
            },
        )
        if res.status_code == 204:
            return True
        else:
            return res.json()

    def delete(self, email):
        res = requests.delete(
            f"{GraphApi.ENDPOINT}/users/{email}",
            headers={**self.auth_header},
        )
        if res.status_code == 204:
            return True
        else:
            return res.json()

    def exists(self, email):
        return (
                requests.get(
                    f"{GraphApi.ENDPOINT}/users/{email}", headers={**self.auth_header},
                ).status_code
                != 404
        )

    def member_of(self, email):
        return requests.get(
            f"{GraphApi.ENDPOINT}/users/{email}/memberOf", headers={**self.auth_header}
        ).json()

    def directory_roles(self, email):
        res = requests.get(
            f"{GraphApi.ENDPOINT}/users/{email}/memberOf", headers={**self.auth_header}
        ).json()
        roles = res.get("value")
        return list(
            filter(
                lambda x: x.get("@odata.type") == "#microsoft.graph.directoryRole",
                roles,
            )
        )

    @property
    def token(self):
        if result := self.cca.acquire_token_silent(scopes=GraphApi.SCOPE, account=None):
            return result.get("access_token")

        return self.cca.acquire_token_for_client(scopes=GraphApi.SCOPE)["access_token"]

    @property
    def auth_header(self):
        return {"Authorization": "Bearer " + self.token}

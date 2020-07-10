import uuid
import msal
from django.urls import reverse

from .settings import AZURE_AUTH


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        AZURE_AUTH.get("CLIENT_ID"),
        authority=authority or AZURE_AUTH.get("AUTHORITY"),
        client_credential=AZURE_AUTH.get("CLIENT_SECRET"),
        token_cache=cache,
    )


def build_auth_url(request, scopes=None, state=None, authority=None):
    if not state:
        state = str(uuid.uuid4())

    request.session["state"] = state

    redirect_uri = request.build_absolute_uri(reverse("azure_auth:login"))

    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [], state=state or str(uuid.uuid4()), redirect_uri=redirect_uri,
    )


def _load_cache(user):
    cache = msal.SerializableTokenCache()
    if user.azure_token_cache:
        cache.deserialize(user.azure_token_cache)
    return cache


def _save_cache(cache: msal.SerializableTokenCache, user):
    if cache.has_state_changed:
        user.azure_token_cache = cache.serialize()
        user.save()

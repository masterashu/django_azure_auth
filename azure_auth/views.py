import msal
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest

from .settings import AZURE_AUTH
from .models import get_user_model
from .utils import _build_msal_app, _save_cache, _load_cache

User = get_user_model()


def logout(request):
    auth_logout(request)
    request.session.clear()

    return redirect(  # Also logout from your tenant's web session
        AZURE_AUTH.get("AUTHORITY")
        + "/oauth2/v2.0/logout"
        + "?post_logout_redirect_uri="
        + request.build_absolute_uri(reverse(AZURE_AUTH.get("LOGIN_REDIRECT_URL")))
    )


def login(request):
    if request.GET.get("state") != request.session.get("state"):
        return redirect("home")  # No-Authentication. Goes back to Homepage
    if "error" in request.GET:  # Authentication/Authorization failure
        return render(request, "auth_error.html", context=request.GET.dict())
    if request.GET.get("code"):
        # Get existing token from session
        cache = msal.SerializableTokenCache()
        if token_cache := request.session.get("token_cache"):
            cache.deserialize(token_cache)

        redirect_uri = request.build_absolute_uri(reverse("azure_auth:login"))

        result: dict = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.GET.get("code"),
            scopes=AZURE_AUTH.get("SCOPE"),
            # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=redirect_uri,
        )

        if "error" in result:
            context = {"result": result}
            return render(request, "registration/auth_error.html", context=context)

        try:
            user = User.objects.get(
                azure_object_id=result.get("id_token_claims").get("oid")
            )
            # Update email id if changed
            if user.email != result.get("id_token_claims").get("preferred_username"):
                user.email = result.get("id_token_claims").get("preferred_username")
                user.save()
            if user.azure_token_cache:
                cache.deserialize(user.azure_token_cache)
        except User.DoesNotExist:
            name = result.get("id_token_claims").get("name").split()

            user = User.objects.create(
                azure_object_id=result.get("id_token_claims").get("oid"),
                email=result.get("id_token_claims").get("preferred_username"),
                first_name=name[0],
                last_name=name[1] if len(name) > 1 else None,
                azure_token_cache=cache.serialize(),
            )
        except:
            return HttpResponseBadRequest()

        auth_login(request, user)

        _save_cache(cache, user)

    return redirect(AZURE_AUTH.get("LOGIN_REDIRECT_URL"))

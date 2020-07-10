import msal

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.views import View

from .forms import UserCreateForm, UserUpdateForm
from .settings import AZURE_AUTH
from .models import get_user_model
from .permissions import UserAdminRequiredMixin
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


class UserCreateView(UserAdminRequiredMixin, View):
    def get(self, request):
        form = UserCreateForm()
        return render(request, "azure_auth/register.html", context={"form": form})

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            from .graph_api import GraphApi

            graph_api = GraphApi()
            res = graph_api.user.create(**form.cleaned_data)
            if res is True:
                return render(request, "azure_auth/register_success.html", context={
                    'email': form.cleaned_data['username'] + AZURE_AUTH.get('DOMAIN')
                })
            else:
                errors = res.get("error").get("message")
        else:
            errors = form.errors
        context = {"form": form, "errors": errors}
        return render(request, "azure_auth/register.html", context=context)


class UserUpdateView(UserAdminRequiredMixin, View):
    def get(self, request, user_id):
        try:
            user = User.objects.get(azure_object_id=user_id)
            user.sync_from_ad()
        except User.DoesNotExist:
            from .graph_api import GraphApi
            res = GraphApi().user.get(user_id)
            if 'error' in request:
                return HttpResponseBadRequest()
            user = User.objects.create(
                azure_object_id=user_id,
                email=res.get('userPrincipalName'),
                first_name=res.get('givenName'),
                last_name=res.get('surname'),
            )
        form = UserUpdateForm(data={
            'username': user.email.split('@')[0],
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
        return render(request, "azure_auth/update.html", context={"form": form})

    def post(self, request, user_id):
        form = UserUpdateForm(request.POST)
        if form.is_valid():
            from .graph_api import GraphApi

            graph_api = GraphApi()
            res = graph_api.user.update(user_id, **form.cleaned_data)
            if res is True:
                try:
                    user = User.objects.get(azure_object_id=user_id)
                    user.sync_from_ad()
                except User.DoesNotExist:
                    return HttpResponseNotFound()
                return render(request, "azure_auth/update.html", context={'user': user})
            else:
                errors = res.get("error").get("message")
        else:
            errors = form.errors
        context = {"form": form, "errors": errors}
        return render(request, "azure_auth/register.html", context=context)


class UserListView(UserAdminRequiredMixin, View):
    def get(self, request):
        from .graph_api import GraphApi
        users = GraphApi().user.list()
        if 'error' in request:
            return HttpResponseNotFound()
        return render(request, 'azure_auth/list.html', context={
            'users': users.get('value')
        })


class UserDeleteView(UserAdminRequiredMixin, View):
    def post(self, request, user_id):
        from .graph_api import GraphApi
        if not GraphApi().user.delete(user_id):
            return HttpResponseBadRequest()
        try:
            user = User.objects.get(azure_object_id=user_id)
            user.delete()
        except User.DoesNotExist:
            return HttpResponse('Deleted')

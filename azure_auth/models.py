from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ImproperlyConfigured
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, password=None, **other_fields):
        user = User(email=email, first_name=first_name)
        if not password:
            password = self.make_random_password()
        user.set_password(password)
        user.save()

    def create_super_user(self, email, first_name, password=None, **other_fields):
        user = User(email=email, first_name=first_name)
        if not password:
            password = self.make_random_password()
        user.set_password(password)
        user.save()

    @staticmethod
    def check_email_availability(self, email: str):
        domain = settings.AZURE_APP.get("DOMAIN")
        if not email.endswith(domain):
            email += domain

        if User.objects.filter(email=email).exists():
            return False


class User(AbstractBaseUser):
    # Object Id of the Azure User
    azure_object_id = models.UUIDField(primary_key=True, editable=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    first_name = models.CharField("First name", max_length=120, blank=False)
    last_name = models.CharField("Last name", max_length=120, blank=True)
    azure_token_cache = models.TextField(null=True, blank=True)
    # Custom Manager
    objects = CustomUserManager()

    USERNAME_FIELD = "email"

    EMAIL_FIELD = "email"

    REQUIRED_FIELDS = [
        "first_name",
    ]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def get_token_from_cache(self, scope=None):
        from .utils import _load_cache, _save_cache, _build_msal_app

        cache = _load_cache(self)
        cca = _build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        if accounts:
            result = cca.acquire_token_silent(scope, account=accounts[0])
            _save_cache(cache, self)
            return result
        else:
            raise Exception


def get_user_model():
    from django.apps import apps as django_apps
    from .settings import AZURE_AUTH

    try:
        return django_apps.get_model(AZURE_AUTH.get("AUTH_USER_MODEL"))
    except ValueError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f'AUTH_USER_MODEL refers to model \'{AZURE_AUTH.get("AUTH_USER_MODEL")}\''
            f" that has not been installed"
        )

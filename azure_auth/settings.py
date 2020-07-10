from django.conf import settings

USER_SETTINGS: dict = getattr(settings, "AZURE_AUTH", {})

AZURE_AUTH = {
    "AUTH_USER_MODEL": USER_SETTINGS.get("AUTH_USER_MODEL", "azure_auth.User"),
    "REDIRECT_PATH": USER_SETTINGS.get("REDIRECT_PATH", "login"),
    "CLIENT_SECRET": USER_SETTINGS.get("CLIENT_SECRET", ""),
    "CLIENT_ID": USER_SETTINGS.get("CLIENT_ID", ""),
    "AUTHORITY": USER_SETTINGS.get("AUTHORITY", ""),
    "DOMAIN": USER_SETTINGS.get('DOMAIN', ''),
    "SCOPE": USER_SETTINGS.get("SCOPE", []),
    "LOGIN_REDIRECT_URL": USER_SETTINGS.get("LOGIN_REDIRECT_URL", "home"),
}

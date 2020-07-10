from django.urls import path
from .views import login, logout
from .settings import AZURE_AUTH

app_name = "azure_auth"
urlpatterns = [
    path(AZURE_AUTH.get("REDIRECT_PATH"), login, name="login"),
    path("logout", logout, name="logout"),
]

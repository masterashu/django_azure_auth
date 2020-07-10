from django.urls import path
from .views import login, logout, UserDeleteView, UserUpdateView
from .settings import AZURE_AUTH

app_name = "azure_auth"
urlpatterns = [
    path(AZURE_AUTH.get("REDIRECT_PATH"), login, name="login"),
    path("logout", logout, name="logout"),
    path("update/<uuid:user_id>", UserUpdateView.as_view(), name='update'),
    path("delete/<uuid:user_id>", UserDeleteView.as_view(), name='delete')
]

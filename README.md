# django_azure_auth

## Installation:
Run `pip install` in your project enviornment to download the package.  
  ```
  pip install git+https://github.com/masterashu/django_azure_auth
  ```

> Note: django_azure_auth requires you to run its migration before other migrations
> since it changes the AUTH_USER_MODEL
> If you need to use custom fields in **User** Model, extend `azure_app.models.User` and 
> mention the same in *settings.py*

## Configuration 

1. Add `azure_auth` to the list of **INSTALLED_APPS**.
    ```python
    INSTALLED_APPS = [
        ...
        'azure_auth',
    ]
    ```
2. Add the following configuration in `project/settings.py`
    ```python
    # Azure Auth Custom User Model

    AUTH_USER_MODEL = "azure_auth.User"

    # Azure App Configurations

    AZURE_APP = {
        "CLIENT_SECRET": "CLIENT_SECRET",
        "CLIENT_ID": "CLIENT_ID",
        "AUTHORITY": "AUTHORITY",
        "DOMAIN": "DOMAIN",
        "REDIRECT_PATH": "REDIRECT_PATH",
        "SCOPE": "SCOPE",
        AUTH_USER_MODEL = "registration.User", # 
    }

    # Microsoft Graph API Endpoint
    ENDPOINT = "https://graph.microsoft.com/v1.0'
    ```
3. Add the azure_auth **urlpatterns** in `project/url.py`
    ```python
    from django.urls import include
    urlpatterns = [
        ...
        path('', include('azure_auth.urls')),
    ]
    ```
4. Run migrations
   ```
   python manage.py migrate azure_app
   python manage.py migrate
   ```
   
## Customization  


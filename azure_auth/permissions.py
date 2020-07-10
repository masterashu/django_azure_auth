from django.contrib.auth.mixins import AccessMixin


class UserAdminRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a superuser."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from .graph_api import GraphApi
        roles = GraphApi().user.directory_roles(request.user.email)
        is_admin = len(list(
            filter(lambda x: x.get('displayName') == 'User Account Administrator', roles)
        )) != 0
        if not is_admin:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

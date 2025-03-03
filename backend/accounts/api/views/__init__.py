from accounts.api.views.auth_views import (
    LoginView, LogoutView, TokenRefreshView, SessionListView,
    SessionEndView, AllSessionsEndView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView
)
from accounts.api.views.user_views import (
    UserViewSet, CurrentUserView, ProfileView, AvatarUpdateView
)
from accounts.api.views.role_views import (
    RoleViewSet, PermissionListView, UserPermissionsView, CreatePermissionView
)

__all__ = [
    'LoginView',
    'LogoutView',
    'TokenRefreshView',
    'SessionListView',
    'SessionEndView',
    'AllSessionsEndView',
    'PasswordChangeView',
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
    'UserViewSet',
    'CurrentUserView',
    'ProfileView',
    'AvatarUpdateView',
    'RoleViewSet',
    'PermissionListView',
    'UserPermissionsView',
    'CreatePermissionView',
]
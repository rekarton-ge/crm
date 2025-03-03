# backend/accounts/api/__init__.py
#
# Этот модуль содержит компоненты REST API для приложения accounts.
# Включает в себя сериализаторы, представления и маршруты для
# управления пользователями, аутентификацией и разрешениями.

from accounts.api.serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, LoginSerializer,
    TokenRefreshSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, RoleMinSerializer, ProfileSerializer,
    ProfileUpdateSerializer, AvatarUpdateSerializer, RoleSerializer,
    RoleCreateSerializer, RoleUpdateSerializer, RoleAssignmentSerializer,
    PermissionSerializer
)

from accounts.api.views import (
    LoginView, LogoutView, TokenRefreshView, SessionListView,
    SessionEndView, AllSessionsEndView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView,
    UserViewSet, CurrentUserView, ProfileView, AvatarUpdateView,
    RoleViewSet, PermissionListView, UserPermissionsView, CreatePermissionView
)

from accounts.api.permissions import (
    IsAdminUser, IsSuperUser, IsOwnerOrAdmin,
    HasPermission, HasRole, CanManageUsers, CanManageRoles
)

__all__ = [
    # Сериализаторы
    'UserListSerializer', 'UserDetailSerializer', 'UserCreateSerializer',
    'UserUpdateSerializer', 'ChangePasswordSerializer', 'LoginSerializer',
    'TokenRefreshSerializer', 'PasswordResetRequestSerializer',
    'PasswordResetConfirmSerializer', 'RoleMinSerializer', 'ProfileSerializer',
    'ProfileUpdateSerializer', 'AvatarUpdateSerializer', 'RoleSerializer',
    'RoleCreateSerializer', 'RoleUpdateSerializer', 'RoleAssignmentSerializer',
    'PermissionSerializer',

    # Представления
    'LoginView', 'LogoutView', 'TokenRefreshView', 'SessionListView',
    'SessionEndView', 'AllSessionsEndView', 'PasswordChangeView',
    'PasswordResetRequestView', 'PasswordResetConfirmView',
    'UserViewSet', 'CurrentUserView', 'ProfileView', 'AvatarUpdateView',
    'RoleViewSet', 'PermissionListView', 'UserPermissionsView', 'CreatePermissionView',

    # Классы разрешений
    'IsAdminUser', 'IsSuperUser', 'IsOwnerOrAdmin',
    'HasPermission', 'HasRole', 'CanManageUsers', 'CanManageRoles',
]
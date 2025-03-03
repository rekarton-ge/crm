from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.api.views import (
    LoginView, LogoutView, TokenRefreshView, SessionListView,
    SessionEndView, AllSessionsEndView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView,
    UserViewSet, CurrentUserView, ProfileView, AvatarUpdateView,
    RoleViewSet, PermissionListView, UserPermissionsView, CreatePermissionView
)

# Настраиваем роутер для ViewSet'ов
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)

urlpatterns = [
    # Маршруты для аутентификации и управления сессиями
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('auth/password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/sessions/', SessionListView.as_view(), name='session_list'),
    path('auth/sessions/<int:pk>/', SessionEndView.as_view(), name='session_end'),
    path('auth/sessions/all/', AllSessionsEndView.as_view(), name='all_sessions_end'),

    # Маршруты для текущего пользователя
    path('users/me/', CurrentUserView.as_view(), name='current_user'),
    path('users/me/profile/', ProfileView.as_view(), name='user_profile'),
    path('users/me/profile/avatar/', AvatarUpdateView.as_view(), name='user_avatar'),

    # Маршруты для разрешений
    path('permissions/', PermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', CreatePermissionView.as_view(), name='create_permission'),
    path('users/me/permissions/', UserPermissionsView.as_view(), name='user_permissions'),

    # Включаем маршруты из роутера
    path('', include(router.urls)),
]
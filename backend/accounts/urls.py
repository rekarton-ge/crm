"""
URL-маршруты для приложения accounts.
"""

from django.urls import path
from accounts.views import (
    LoginView,
    RegisterView,
    UserProfileView,
    UserSessionListView,
    UserSessionDetailView,
    EndAllSessionsView
)

app_name = 'accounts'

urlpatterns = [
    # Аутентификация
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    
    # Профиль пользователя
    path('users/me/profile/', UserProfileView.as_view(), name='profile'),
    
    # Сессии
    path('auth/sessions/', UserSessionListView.as_view(), name='sessions'),
    path('auth/sessions/<int:pk>/', UserSessionDetailView.as_view(), name='session-detail'),
    path('auth/sessions/end-all/', EndAllSessionsView.as_view(), name='end-all-sessions'),
]
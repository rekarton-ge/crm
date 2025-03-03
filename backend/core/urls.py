"""
URL-маршруты для модуля Core.

Этот модуль содержит URL-маршруты для модуля Core.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views import (
    SettingViewSet, TagViewSet, TaggedItemViewSet, FileUploadViewSet
)
from core.api.views.categories import CategoryViewSet

# Создаем роутер для API
router = DefaultRouter()
router.register(r'settings', SettingViewSet, basename='setting')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'tagged-items', TaggedItemViewSet, basename='tagged-item')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'files', FileUploadViewSet, basename='file')

app_name = 'core'

urlpatterns = [
    # API маршруты
    path('api/', include((router.urls, 'api'), namespace='api')),
]

"""
Тесты для приложения accounts.
"""

from django.conf import settings

# Настройки для тестов
settings.TRACK_ALL_USER_REQUESTS = True
settings.ACTIVITY_EXCLUDE_PATHS = [
    '/api/auth/token/refresh/',
    '/api/accounts/auth/sessions/',
    '/static/',
    '/media/',
    '/favicon.ico',
]

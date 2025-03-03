"""
Базовые классы middleware для аутентификации и авторизации.
"""

import re
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAuthenticationMiddleware(MiddlewareMixin):
    """
    Базовый класс для middleware аутентификации.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.bearer_pattern = re.compile(r'Bearer\s+(.+)')

    def _is_excluded_url(self, path):
        """
        Проверяет, нужно ли исключить URL из обработки.
        """
        excluded_urls = getattr(settings, 'AUTH_EXCLUDED_URLS', [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico'
        ])
        return any(path.startswith(url) for url in excluded_urls)

    def _get_token_from_header(self, request):
        """
        Извлекает токен из заголовка Authorization.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        match = self.bearer_pattern.match(auth_header)
        return match.group(1) if match else None

    def _get_client_ip(self, request):
        """
        Получает IP-адрес клиента из запроса.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '') 
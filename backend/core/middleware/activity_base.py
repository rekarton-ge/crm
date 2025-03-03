"""
Базовый класс middleware для отслеживания активности пользователей.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseActivityMiddleware(MiddlewareMixin):
    """
    Базовый класс для отслеживания активности пользователей.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.track_all_requests = getattr(settings, 'TRACK_ALL_USER_REQUESTS', False)
        self.exclude_paths = getattr(settings, 'ACTIVITY_EXCLUDE_PATHS', [
            '/static/',
            '/media/',
            '/favicon.ico',
        ])
        self.activity_types = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }

    def _should_log_activity(self, request):
        """
        Проверяет, нужно ли записывать активность для данного запроса.
        """
        if self.track_all_requests:
            return not any(request.path.startswith(path) for path in self.exclude_paths)
        
        return (
            request.path.startswith('/api/') and
            not any(request.path.startswith(path) for path in self.exclude_paths)
        )

    def _get_activity_type(self, request):
        """
        Определяет тип активности на основе метода запроса.
        """
        return self.activity_types.get(request.method, 'other')

    def _get_object_info(self, request):
        """
        Извлекает информацию об объекте из запроса.
        """
        object_type = ''
        object_id = ''

        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'api':
            module = path_parts[1] if len(path_parts) > 1 else ''
            model = path_parts[2] if len(path_parts) > 2 else ''
            if len(path_parts) > 3 and path_parts[3].isdigit():
                object_id = path_parts[3]

            if module and model:
                object_type = f"{module}.{model}"

        return object_type, object_id

    def _get_activity_description(self, request, response):
        """
        Формирует описание активности.
        """
        method = request.method
        path = request.path
        description = f"{method} {path}"

        if method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'data'):
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            
            # Скрываем конфиденциальные поля
            sensitive_fields = ['password', 'password1', 'password2', 'token', 'access', 'refresh']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '***'

            if data:
                description += f" - Данные: {data}"

        return description

    def _get_client_ip(self, request):
        """
        Получает IP-адрес клиента.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '') 
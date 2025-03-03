"""
Middleware для аутентификации и отслеживания активности пользователей.
"""

import logging
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from accounts.models import UserSession, UserActivity
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthenticationMiddleware:
    """
    Middleware для аутентификации пользователей через JWT токен.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._authenticate_user(request)
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._update_user_session(request)
        return self.get_response(request)

    def _authenticate_user(self, request):
        """Аутентифицирует пользователя по JWT токену"""
        if not hasattr(request, 'user'):
            request.user = AnonymousUser()

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return

        try:
            token = auth_header.split(' ')[1]
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            
            try:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    logger.warning(f"Пользователь {user.username} не активен")
                    return
                request.user = user
            except User.DoesNotExist:
                logger.warning(f"Пользователь с id={user_id} не найден")
                return
                
        except TokenError as e:
            logger.warning(f"Ошибка при аутентификации: {str(e)}")
            return

    def _update_user_session(self, request):
        """Обновляет или создает сессию пользователя"""
        try:
            session_key = request.headers.get('Authorization', '').split(' ')[1]
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            session, created = UserSession.objects.get_or_create(
                user=request.user,
                session_key=session_key,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'device_type': self._get_device_type(user_agent)
                }
            )

            if not created:
                session.update_activity()

            # Завершаем все другие активные сессии
            UserSession.objects.filter(
                user=request.user,
                ended_at__isnull=True
            ).exclude(id=session.id).update(ended_at=timezone.now())

            request.user_session = session
        except Exception as e:
            logger.error(f"Ошибка при обновлении сессии: {str(e)}")

    def _get_client_ip(self, request):
        """Получает IP-адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _get_device_type(self, user_agent):
        """Определяет тип устройства на основе User-Agent"""
        user_agent = user_agent.lower()
        if 'mobile' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent:
            return 'tablet'
        elif 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent:
            return 'desktop'
        return 'other'


class UserActivityMiddleware:
    """
    Middleware для отслеживания активности пользователей.
    """

    EXCLUDED_PATHS = ['/api/auth/', '/api/static/', '/api/media/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if self._should_log_activity(request, response):
            self._log_activity(request, response)
            
        return response

    def _should_log_activity(self, request, response):
        """Проверяет, нужно ли логировать активность"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False

        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return False

        if response.status_code >= 400:
            return False

        return True

    def _log_activity(self, request, response):
        """Логирует активность пользователя"""
        try:
            activity_type = 'view'  # Используем 'view' вместо request.method
            description = request.path
            session = getattr(request, 'user_session', None)

            UserActivity.objects.create(
                user=request.user,
                session=session,
                activity_type=activity_type,
                description=description,
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
        except Exception as e:
            logger.error(f"Ошибка при логировании активности: {str(e)}")
"""
Middleware для аутентификации и отслеживания активности пользователей.
"""

import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from core.middleware.auth_base import BaseAuthenticationMiddleware
from core.middleware.activity_base import BaseActivityMiddleware
from accounts.models import UserSession, UserActivity
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(BaseAuthenticationMiddleware):
    """
    Middleware для аутентификации через JWT токены.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        # Добавляем дополнительные пути к исключениям
        self.excluded_urls = [
            '/api/token/',
            '/api/token/refresh/',
            '/api/accounts/auth/login/',
            '/api/accounts/auth/register/',
            '/api/accounts/auth/sessions/',
            '/api/accounts/auth/sessions/end-all/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/'
        ]

    def _is_excluded_url(self, path):
        """
        Проверяет, нужно ли исключить URL из обработки.
        """
        # Для статических файлов и админки используем startswith
        static_paths = ['/static/', '/media/', '/favicon.ico', '/admin/']
        if any(path.startswith(url) for url in static_paths):
            return True
            
        # Для API эндпоинтов используем точное сравнение
        api_paths = [url for url in self.excluded_urls if url not in static_paths]
        return path in api_paths

    def __call__(self, request):
        if self._is_excluded_url(request.path):
            return self.get_response(request)

        token = self._get_token_from_header(request)
        if token:
            user = self._authenticate_with_token(token)
            if user:
                request.user = user
                self._update_user_session(request, token)

        return self.get_response(request)

    def _authenticate_with_token(self, token):
        """
        Аутентифицирует пользователя по JWT токену.
        """
        try:
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            if not user_id:
                return None

            user = User.objects.get(id=user_id)

            if not user.is_active:
                logger.warning(f"Пользователь {user.username} не активен")
                return None

            if hasattr(user, 'is_locked') and user.is_locked():
                logger.warning(f"Аккаунт пользователя {user.username} заблокирован")
                return None

            return user

        except (TokenError, InvalidToken, User.DoesNotExist, Exception) as e:
            logger.warning(f"Ошибка при аутентификации: {str(e)}")
            return None

    def _update_user_session(self, request, token):
        """
        Обновляет или создает запись о сессии пользователя.
        """
        try:
            # Проверяем наличие активной сессии с этим токеном
            session = UserSession.objects.filter(
                user=request.user,
                session_key=token,
                ended_at__isnull=True
            ).first()

            if session:
                session.last_activity = timezone.now()
                session.save(update_fields=['last_activity'])
            else:
                # Создаем новую сессию только если это запрос на вход или регистрацию
                if request.path in ['/api/accounts/auth/login/', '/api/accounts/auth/register/']:
                    # Проверяем наличие других активных сессий для этого пользователя
                    active_sessions = UserSession.objects.filter(
                        user=request.user,
                        ended_at__isnull=True
                    )
                    
                    # Если есть активные сессии, завершаем их
                    if active_sessions.exists():
                        active_sessions.update(ended_at=timezone.now())
                    
                    # Создаем новую сессию
                    UserSession.objects.create(
                        user=request.user,
                        session_key=token,
                        ip_address=self._get_client_ip(request),
                        started_at=timezone.now(),
                        last_activity=timezone.now()
                    )
                else:
                    # Для всех остальных запросов, если нет активной сессии с этим токеном,
                    # используем любую другую активную сессию пользователя
                    active_session = UserSession.objects.filter(
                        user=request.user,
                        ended_at__isnull=True
                    ).first()
                    
                    if active_session:
                        active_session.last_activity = timezone.now()
                        active_session.save(update_fields=['last_activity'])
        except Exception as e:
            logger.error(f"Ошибка при обновлении сессии: {str(e)}")

    def _get_client_ip(self, request):
        """
        Получает IP-адрес клиента из запроса.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class UserActivityMiddleware(BaseActivityMiddleware):
    """
    Middleware для отслеживания активности пользователей.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.exclude_paths.extend([
            '/api/token/',
            '/api/token/refresh/',
            '/api/accounts/auth/login/',
            '/api/accounts/auth/register/',
            '/api/accounts/auth/sessions/',
            '/api/accounts/auth/sessions/end-all/',
            '/static/',
            '/media/',
            '/favicon.ico'
        ])

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and self._should_log_activity(request):
            self._log_user_activity(request, response)

        return response

    def _log_user_activity(self, request, response):
        """
        Записывает активность пользователя.
        """
        try:
            # Проверяем статус ответа
            if response.status_code >= 400:
                return

            activity_type = self._get_activity_type(request)
            object_type, object_id = self._get_object_info(request)
            description = self._get_activity_description(request, response)

            UserActivity.objects.create(
                user=request.user,
                session=self._get_user_session(request),
                activity_type=activity_type,
                description=description,
                ip_address=self._get_client_ip(request),
                object_type=object_type,
                object_id=object_id
            )
        except Exception as e:
            logger.error(f"Ошибка при записи активности пользователя: {str(e)}")

    def _get_user_session(self, request):
        """
        Получает текущую сессию пользователя.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            return UserSession.objects.filter(
                session_key=token,
                ended_at=None
            ).first()
        return None
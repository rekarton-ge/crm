import re
import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from accounts.models import UserSession, UserActivity

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware для аутентификации через JWT токены.

    Извлекает JWT токен из заголовков запроса, проверяет его валидность
    и устанавливает пользователя в request.user. Также обновляет
    соответствующую запись UserSession и время последней активности.

    Это дополнительный уровень аутентификации, который работает с
    аутентификацией Django REST Framework.
    """

    def __init__(self, get_response):
        """
        Инициализация middleware.
        """
        self.get_response = get_response
        # Компилируем регулярное выражение для извлечения токена один раз
        self.bearer_pattern = re.compile(r'Bearer\s+(.+)')

    def __call__(self, request):
        """
        Обрабатывает запрос до и после его выполнения.
        """
        # Пропускаем обработку для встроенных URL Django
        if self._is_django_admin_url(request.path):
            return self.get_response(request)

        # Получаем токен из заголовков
        token = self._get_jwt_token(request)
        if token:
            # Если токен найден, пытаемся аутентифицировать пользователя
            user = self._authenticate_with_token(token)
            if user:
                # Устанавливаем пользователя в запросе
                request.user = user
                # Обновляем сессию
                self._update_user_session(request, token)

        # Получаем ответ от следующего middleware или view
        response = self.get_response(request)

        return response

    def _is_django_admin_url(self, path):
        """
        Проверяет, является ли URL частью админки Django.
        """
        django_urls = ['/admin/', '/static/']
        return any(path.startswith(url) for url in django_urls)

    def _get_jwt_token(self, request):
        """
        Извлекает JWT токен из заголовков запроса.
        """
        # Получаем заголовок авторизации
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        # Ищем токен в формате "Bearer <token>"
        match = self.bearer_pattern.match(auth_header)
        if match:
            return match.group(1)

        return None

    def _authenticate_with_token(self, token):
        """
        Аутентифицирует пользователя по JWT токену.
        """
        try:
            # Проверяем токен
            access_token = AccessToken(token)

            # Получаем ID пользователя из токена
            user_id = access_token.get('user_id')
            if not user_id:
                return None

            # Получаем пользователя
            user = User.objects.get(id=user_id)

            # Проверяем, что пользователь активен
            if not user.is_active:
                logger.warning(f"Пользователь {user.username} не активен")
                return None

            # Проверяем, не заблокирован ли аккаунт
            if user.is_locked():
                logger.warning(f"Аккаунт пользователя {user.username} заблокирован")
                return None

            return user

        except (TokenError, InvalidToken) as e:
            logger.warning(f"Ошибка при проверке токена: {str(e)}")
            return None
        except User.DoesNotExist:
            logger.warning(f"Пользователь с ID {user_id} не найден")
            return None
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {str(e)}")
            return None

    def _update_user_session(self, request, token):
        """
        Обновляет запись о сессии пользователя.
        """
        try:
            # Ищем сессию по токену
            session = UserSession.objects.filter(
                session_key=token,
                ended_at=None
            ).first()

            if session:
                # Обновляем время последней активности
                session.last_activity = timezone.now()
                session.save(update_fields=['last_activity'])
        except Exception as e:
            logger.error(f"Ошибка при обновлении сессии: {str(e)}")


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware для отслеживания активности пользователей.

    Записывает действия пользователя в журнал активности.
    """

    def __init__(self, get_response):
        """
        Инициализация middleware.
        """
        self.get_response = get_response
        # Настройки для отслеживания активности
        self.track_all_requests = getattr(settings, 'TRACK_ALL_USER_REQUESTS', False)
        self.exclude_paths = getattr(settings, 'ACTIVITY_EXCLUDE_PATHS', [
            '/api/auth/token/refresh/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/api/accounts/auth/sessions/',
        ])
        self.activity_types = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }

    def __call__(self, request):
        """
        Обрабатывает запрос до и после его выполнения.
        """
        # Получаем ответ от следующего middleware или view
        response = self.get_response(request)

        # Если пользователь аутентифицирован, записываем активность
        if request.user.is_authenticated:
            self._log_user_activity(request, response)

        return response

    def _should_log_activity(self, request):
        """
        Проверяет, нужно ли записывать активность для данного запроса.
        """
        # Если отслеживаем все запросы, проверяем только исключения
        if self.track_all_requests:
            return not any(request.path.startswith(path) for path in self.exclude_paths)

        # Иначе отслеживаем только определенные типы запросов для определенных URL
        # Например, запросы к API
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

        Возвращает кортеж (object_type, object_id).
        """
        # По умолчанию нет информации об объекте
        object_type = ''
        object_id = ''

        # Извлекаем информацию из URL
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'api':
            # Например, /api/accounts/users/1/
            # module = accounts, model = users, id = 1
            module = path_parts[1] if len(path_parts) > 1 else ''
            model = path_parts[2] if len(path_parts) > 2 else ''
            if len(path_parts) > 3 and path_parts[3].isdigit():
                object_id = path_parts[3]

            if module and model:
                object_type = f"{module}.{model}"

        return object_type, object_id

    def _get_activity_description(self, request, response):
        """
        Формирует описание активности на основе запроса и ответа.
        """
        method = request.method
        path = request.path

        # Базовое описание
        description = f"{method} {path}"

        # Если это запрос с телом, добавляем информацию о параметрах
        # (без конфиденциальных данных)
        if method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'data'):
            # Копируем данные, чтобы не изменять оригинал
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

            # Скрываем конфиденциальные поля
            sensitive_fields = ['password', 'password1', 'password2', 'token', 'access', 'refresh']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '***'

            # Добавляем данные к описанию, если они есть
            if data:
                description += f" - Данные: {data}"

        # Добавляем статус ответа
        description += f" - Статус: {response.status_code}"

        return description

    def _log_user_activity(self, request, response):
        """
        Записывает активность пользователя в журнал.
        """
        if not self._should_log_activity(request):
            return

        try:
            # Получаем тип активности
            activity_type = self._get_activity_type(request)

            # Получаем информацию об объекте
            object_type, object_id = self._get_object_info(request)

            # Формируем описание
            description = self._get_activity_description(request, response)

            # Получаем IP-адрес
            ip_address = self._get_client_ip(request)

            # Получаем сессию пользователя, если есть
            session = self._get_user_session(request)

            # Записываем активность
            UserActivity.objects.create(
                user=request.user,
                session=session,
                activity_type=activity_type,
                description=description,
                timestamp=timezone.now(),
                ip_address=ip_address,
                object_type=object_type,
                object_id=object_id
            )

        except Exception as e:
            logger.error(f"Ошибка при записи активности пользователя: {str(e)}")

    def _get_client_ip(self, request):
        """
        Получает IP-адрес клиента.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For может содержать список IP-адресов, берем первый
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_user_session(self, request):
        """
        Получает текущую сессию пользователя.
        """
        # Получаем токен из заголовков
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        match = re.match(r'Bearer\s+(.+)', auth_header)

        if match:
            token = match.group(1)
            try:
                return UserSession.objects.filter(
                    session_key=token,
                    user=request.user,
                    ended_at=None
                ).first()
            except Exception:
                return None

        return None
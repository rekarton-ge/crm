import re
import logging
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

# Получаем модель пользователя
User = get_user_model()
logger = logging.getLogger(__name__)


def generate_token(user, expires_delta=None):
    """
    Генерирует JWT токены для указанного пользователя.

    Args:
        user (User): Пользователь, для которого генерируются токены
        expires_delta (timedelta, optional): Срок действия токена доступа.
                                            По умолчанию None (используются настройки)

    Returns:
        dict: Словарь с токенами доступа и обновления
    """
    try:
        # Создаем токен обновления для пользователя
        refresh = RefreshToken.for_user(user)

        # Если указан срок действия, устанавливаем его
        if expires_delta:
            refresh.access_token.set_exp(lifetime=expires_delta)

        # Добавляем дополнительные данные в токен
        refresh.access_token.payload.update({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })

        if hasattr(user, 'roles'):
            # Добавляем роли пользователя в токен
            roles = list(user.roles.values_list('name', flat=True))
            refresh.access_token.payload.update({
                'roles': roles
            })

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    except Exception as e:
        logger.error(f"Ошибка при генерации токена: {e}")
        return None


def validate_token(token, token_type='access'):
    """
    Проверяет валидность JWT токена.

    Args:
        token (str): Токен для проверки
        token_type (str, optional): Тип токена ('access' или 'refresh'). По умолчанию 'access'

    Returns:
        bool: True, если токен валидный, иначе False
    """
    try:
        # Создаем соответствующий объект токена
        if token_type == 'access':
            from rest_framework_simplejwt.tokens import AccessToken
            token_obj = AccessToken(token)
        else:
            from rest_framework_simplejwt.tokens import RefreshToken
            token_obj = RefreshToken(token)

        # Проверяем валидность токена (этот вызов вызовет исключение, если токен невалидный)
        _ = token_obj.payload
        return True

    except TokenError:
        # Токен невалидный или просрочен
        return False

    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {e}")
        return False


def extract_token(request):
    """
    Извлекает JWT токен из заголовков запроса.

    Args:
        request (HttpRequest): Объект запроса Django

    Returns:
        str or None: Строка с токеном или None, если токен не найден
    """
    # Получаем заголовок авторизации
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    # Ищем токен в формате "Bearer <token>"
    match = re.match(r'Bearer\s+(.+)', auth_header)
    if match:
        return match.group(1)

    return None


def get_user_from_token(token):
    """
    Получает пользователя по JWT токену.

    Args:
        token (str): JWT токен

    Returns:
        User or None: Объект пользователя или None, если пользователь не найден
    """
    try:
        # Создаем объект токена
        from rest_framework_simplejwt.tokens import AccessToken
        token_obj = AccessToken(token)

        # Получаем ID пользователя из токена
        user_id = token_obj.get('user_id')
        if not user_id:
            return None

        # Получаем пользователя из базы данных
        user = User.objects.get(id=user_id)

        # Проверяем активность пользователя
        if not user.is_active:
            logger.warning(f"Пользователь {user.username} не активен")
            return None

        # Проверяем, не заблокирован ли аккаунт
        if hasattr(user, 'is_locked') and user.is_locked():
            logger.warning(f"Аккаунт пользователя {user.username} заблокирован")
            return None

        return user

    except User.DoesNotExist:
        logger.warning(f"Пользователь с ID {user_id} не найден")
        return None

    except Exception as e:
        logger.error(f"Ошибка при получении пользователя из токена: {e}")
        return None


def create_jwt_response(user, request=None):
    """
    Создает ответ с JWT токенами для указанного пользователя.
    Также сохраняет информацию о сессии, если request предоставлен.

    Args:
        user (User): Пользователь, для которого создаются токены
        request (HttpRequest, optional): Объект запроса Django. По умолчанию None

    Returns:
        dict: Словарь с токенами и информацией о пользователе
    """
    from accounts.services import AuthService

    # Генерируем токены
    tokens = generate_token(user)
    if not tokens:
        return {
            'error': _('Ошибка при генерации токенов')
        }

    # Обновляем время последнего входа
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    # Если предоставлен запрос, сохраняем информацию о сессии
    if request and hasattr(AuthService, 'create_user_session'):
        try:
            AuthService.create_user_session(user, request, tokens['refresh'])
        except Exception as e:
            logger.error(f"Ошибка при создании сессии: {e}")

    # Подготавливаем данные о пользователе
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
    }

    # Добавляем роли, если они есть
    if hasattr(user, 'roles'):
        user_data['roles'] = list(user.roles.values('id', 'name'))

    # Формируем ответ
    response = {
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh'],
        'user': user_data
    }

    return response


def get_client_ip(request):
    """
    Получает IP-адрес клиента из запроса.

    Args:
        request (HttpRequest): Объект запроса Django

    Returns:
        str: IP-адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For может содержать список IP-адресов, берем первый
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent_info(request):
    """
    Получает информацию о User-Agent клиента.

    Args:
        request (HttpRequest): Объект запроса Django

    Returns:
        dict: Словарь с информацией о User-Agent
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Определяем тип устройства
    device_type = 'other'
    if 'Mobile' in user_agent:
        device_type = 'mobile'
    elif 'Tablet' in user_agent:
        device_type = 'tablet'
    else:
        device_type = 'desktop'

    return {
        'user_agent': user_agent,
        'device_type': device_type
    }


def generate_unique_token():
    """
    Генерирует уникальный токен для однократного использования.

    Returns:
        str: Уникальный токен
    """
    return str(uuid.uuid4())
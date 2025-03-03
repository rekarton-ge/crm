"""
Утилиты для работы с паролями в приложении accounts.
"""

from django.contrib.auth import get_user_model
import logging
from core.utils.password_security import (
    generate_password,
    validate_password_strength,
    check_common_passwords,
    generate_password_reset_token,
    validate_password_reset_token,
)
from core.utils.security_utils import encrypt_data, decrypt_data

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_user_password():
    """
    Генерирует пароль для нового пользователя с учетом политик безопасности.
    """
    return generate_password(length=12, include_digits=True, include_special=True)


def validate_user_password(password):
    """
    Проверяет пароль пользователя на соответствие всем требованиям безопасности.
    """
    # Проверяем базовую надежность пароля
    is_valid, error_message = validate_password_strength(
        password,
        min_length=8,
        require_uppercase=True,
        require_digits=True,
        require_special=True
    )
    
    if not is_valid:
        return False, error_message

    # Проверяем, не является ли пароль распространенным
    if not check_common_passwords(password):
        return False, "Этот пароль слишком распространен. Пожалуйста, выберите более уникальный пароль."

    return True, ""


def handle_password_reset(user):
    """
    Обрабатывает запрос на сброс пароля для пользователя.
    
    Args:
        user: Объект пользователя

    Returns:
        tuple: (User, bool) - объект пользователя и статус успешности операции
    """
    try:
        # Проверяем, что пользователь активен
        if not user.is_active:
            logger.warning(f"Попытка сброса пароля для неактивного пользователя: {user.username}")
            return user, False

        # Проверяем, не заблокирован ли пользователь
        if hasattr(user, 'is_locked') and user.is_locked():
            logger.warning(f"Попытка сброса пароля для заблокированного пользователя: {user.username}")
            return user, False

        # Генерируем токен для сброса пароля
        uid, token = generate_password_reset_token(user)
        
        # Здесь может быть дополнительная логика, специфичная для accounts
        # Например, отправка email, сохранение в историю и т.д.
        
        return user, True
    except Exception as e:
        logger.error(f"Ошибка при обработке сброса пароля для пользователя {user.username}: {e}")
        return user, False


def verify_reset_token(uidb64, token):
    """
    Проверяет токен сброса пароля с учетом специфики приложения accounts.
    """
    user = validate_password_reset_token(uidb64, token, User)
    
    if user:
        # Проверяем дополнительные условия, специфичные для accounts
        if hasattr(user, 'is_locked') and user.is_locked():
            logger.warning(f"Попытка сброса пароля для заблокированного пользователя: {user.username}")
            return None
            
    return user


def encrypt_user_data(data):
    """
    Шифрует чувствительные данные пользователя.
    """
    return encrypt_data(data)


def decrypt_user_data(encrypted_data):
    """
    Расшифровывает чувствительные данные пользователя.
    """
    return decrypt_data(encrypted_data)
"""
Утилиты для работы с паролями и их безопасностью.
"""

import random
import string
import re
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import logging

logger = logging.getLogger(__name__)


def generate_password(length=12, include_digits=True, include_special=True):
    """
    Генерирует случайный надежный пароль.
    """
    # Определяем наборы символов
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits if include_digits else ''
    special = "!@#$%^&*()_-+=<>?/[]{}|" if include_special else ''

    # Объединяем все наборы символов
    all_chars = lowercase + uppercase + digits + special

    # Обязательные символы (минимум 1 из каждой категории)
    required_chars = [
        random.choice(lowercase),
        random.choice(uppercase),
    ]

    if include_digits:
        required_chars.append(random.choice(digits))

    if include_special:
        required_chars.append(random.choice(special))

    # Генерируем оставшуюся часть пароля
    remaining_length = length - len(required_chars)
    remaining_chars = [random.choice(all_chars) for _ in range(remaining_length)]

    # Объединяем и перемешиваем все символы
    all_password_chars = required_chars + remaining_chars
    random.shuffle(all_password_chars)

    return ''.join(all_password_chars)


def validate_password_strength(password, min_length=8, require_uppercase=True,
                           require_digits=True, require_special=True):
    """
    Проверяет надежность пароля.
    """
    if len(password) < min_length:
        return False, _("Пароль должен содержать не менее %(min_length)d символов.") % {'min_length': min_length}

    if require_uppercase and not re.search(r'[A-Z]', password):
        return False, _("Пароль должен содержать хотя бы одну заглавную букву.")

    if require_digits and not re.search(r'\d', password):
        return False, _("Пароль должен содержать хотя бы одну цифру.")

    if require_special and not re.search(r'[!@#$%^&*()_\-+=<>?/\[\]{}|]', password):
        return False, _("Пароль должен содержать хотя бы один специальный символ.")

    return True, ""


def check_common_passwords(password):
    """
    Проверяет, не входит ли пароль в список распространенных паролей.
    """
    common_passwords = [
        "123456", "password", "123456789", "12345678", "12345", "1234567", "1234567890",
        "qwerty", "abc123", "111111", "123123", "admin", "welcome", "monkey", "login",
        "qwerty123", "123qwe", "1q2w3e4r", "passw0rd", "qwertyuiop"
    ]
    return password.lower() not in common_passwords


class CorePasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Базовый генератор токенов для сброса пароля.
    """
    def _make_hash_value(self, user, timestamp):
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return (
            str(user.pk) + str(timestamp) + str(user.password) +
            str(login_timestamp) + str(user.is_active)
        )


# Создаем экземпляр генератора токенов
password_reset_token_generator = CorePasswordResetTokenGenerator()


def generate_password_reset_token(user):
    """
    Генерирует токен для сброса пароля.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)
    return uid, token


def validate_password_reset_token(uidb64, token, user_model):
    """
    Проверяет валидность токена для сброса пароля.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = user_model.objects.get(pk=uid)

        if password_reset_token_generator.check_token(user, token):
            if not user.is_active:
                logger.warning(f"Попытка сбросить пароль для неактивного пользователя: {user.username}")
                return None

            return user

    except Exception as e:
        logger.error(f"Ошибка при проверке токена сброса пароля: {e}")

    return None 
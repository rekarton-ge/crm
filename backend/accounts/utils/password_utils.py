import random
import string
import re
import logging
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_password(length=12, include_digits=True, include_special=True):
    """
    Генерирует случайный надежный пароль.

    Args:
        length (int, optional): Длина пароля. По умолчанию 12.
        include_digits (bool, optional): Включать ли цифры. По умолчанию True.
        include_special (bool, optional): Включать ли специальные символы. По умолчанию True.

    Returns:
        str: Сгенерированный пароль
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

    Args:
        password (str): Пароль для проверки
        min_length (int, optional): Минимальная длина пароля. По умолчанию 8.
        require_uppercase (bool, optional): Требовать ли заглавные буквы. По умолчанию True.
        require_digits (bool, optional): Требовать ли цифры. По умолчанию True.
        require_special (bool, optional): Требовать ли спецсимволы. По умолчанию True.

    Returns:
        tuple: (bool, str) - Результат проверки и сообщение об ошибке (если есть)
    """
    # Проверяем длину
    if len(password) < min_length:
        return False, _("Пароль должен содержать не менее %(min_length)d символов.") % {'min_length': min_length}

    # Проверяем наличие заглавных букв
    if require_uppercase and not re.search(r'[A-Z]', password):
        return False, _("Пароль должен содержать хотя бы одну заглавную букву.")

    # Проверяем наличие цифр
    if require_digits and not re.search(r'\d', password):
        return False, _("Пароль должен содержать хотя бы одну цифру.")

    # Проверяем наличие специальных символов
    if require_special and not re.search(r'[!@#$%^&*()_\-+=<>?/\[\]{}|]', password):
        return False, _("Пароль должен содержать хотя бы один специальный символ.")

    return True, ""


def check_common_passwords(password):
    """
    Проверяет, не входит ли пароль в список распространенных паролей.

    Args:
        password (str): Пароль для проверки

    Returns:
        bool: True, если пароль безопасный, иначе False
    """
    # Список 20 самых распространенных паролей
    common_passwords = [
        "123456", "password", "123456789", "12345678", "12345", "1234567", "1234567890",
        "qwerty", "abc123", "111111", "123123", "admin", "welcome", "monkey", "login",
        "qwerty123", "123qwe", "1q2w3e4r", "passw0rd", "qwertyuiop"
    ]

    return password.lower() not in common_passwords


class AccountPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Генератор токенов для сброса пароля с дополнительной проверкой,
    что пользователь активен и не заблокирован.
    """

    def _make_hash_value(self, user, timestamp):
        """
        Создает хеш для генерации токена.
        Включает последнее время изменения пароля и статус активности.
        """
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)

        # Создаем хеш с учетом статуса пользователя и времени последнего входа
        return (
                str(user.pk) + str(timestamp) + str(user.password) +
                str(login_timestamp) + str(user.is_active)
        )


# Создаем экземпляр генератора токенов для сброса пароля
password_reset_token_generator = AccountPasswordResetTokenGenerator()


def generate_password_reset_token(user):
    """
    Генерирует токен для сброса пароля и кодирует его вместе с ID пользователя.

    Args:
        user (User): Пользователь, для которого генерируется токен

    Returns:
        tuple: (uid, token) - Закодированный ID пользователя и токен
    """
    # Кодируем ID пользователя
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Генерируем токен
    token = password_reset_token_generator.make_token(user)

    return uid, token


def validate_password_reset_token(uidb64, token):
    """
    Проверяет валидность токена для сброса пароля и возвращает соответствующего пользователя.

    Args:
        uidb64 (str): Закодированный ID пользователя
        token (str): Токен для сброса пароля

    Returns:
        User or None: Пользователь, если токен валидный, иначе None
    """
    try:
        # Декодируем ID пользователя
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        # Проверяем токен
        if password_reset_token_generator.check_token(user, token):
            # Проверяем, что пользователь активен
            if not user.is_active:
                logger.warning(f"Попытка сбросить пароль для неактивного пользователя: {user.username}")
                return None

            # Проверяем, не заблокирован ли аккаунт
            if hasattr(user, 'is_locked') and user.is_locked():
                logger.warning(f"Попытка сбросить пароль для заблокированного пользователя: {user.username}")
                return None

            return user

    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        logger.error(f"Ошибка при проверке токена сброса пароля: {e}")

    return None


def encrypt_sensitive_data(data):
    """
    Шифрует чувствительные данные.

    Args:
        data (str): Данные для шифрования

    Returns:
        str: Зашифрованные данные
    """
    try:
        from cryptography.fernet import Fernet
        from django.conf import settings

        # Получаем ключ шифрования из настроек
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            logger.error("Ключ шифрования не найден в настройках")
            return None

        # Создаем объект Fernet для шифрования
        cipher_suite = Fernet(key)

        # Шифруем данные
        cipher_text = cipher_suite.encrypt(force_bytes(data))
        return cipher_text.decode('utf-8')

    except Exception as e:
        logger.error(f"Ошибка при шифровании данных: {e}")
        return None


def decrypt_sensitive_data(encrypted_data):
    """
    Расшифровывает чувствительные данные.

    Args:
        encrypted_data (str): Зашифрованные данные

    Returns:
        str: Расшифрованные данные
    """
    try:
        from cryptography.fernet import Fernet
        from django.conf import settings

        # Получаем ключ шифрования из настроек
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            logger.error("Ключ шифрования не найден в настройках")
            return None

        # Создаем объект Fernet для расшифровки
        cipher_suite = Fernet(key)

        # Расшифровываем данные
        plain_text = cipher_suite.decrypt(force_bytes(encrypted_data))
        return plain_text.decode('utf-8')

    except Exception as e:
        logger.error(f"Ошибка при расшифровке данных: {e}")
        return None
"""
Тесты для утилит приложения accounts.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.utils.password_utils import (
    generate_user_password,
    validate_user_password,
    handle_password_reset,
    verify_reset_token,
    encrypt_user_data,
    decrypt_user_data
)
from core.tests.test_base import BaseTestCase

User = get_user_model()


class PasswordUtilsTest(BaseTestCase):
    """
    Тесты для утилит работы с паролями.
    """

    def test_password_generation(self):
        """
        Тест генерации пароля.
        """
        password = generate_user_password()
        is_valid, message = validate_user_password(password)
        self.assertTrue(is_valid, f"Сгенерированный пароль не прошел валидацию: {message}")
        self.assertGreaterEqual(len(password), 12)

    def test_password_validation(self):
        """
        Тест валидации паролей.
        """
        # Тест слабых паролей
        weak_passwords = [
            "password123",  # Слишком простой
            "12345678",    # Только цифры
            "qwertyui",    # Только буквы
            "short",       # Слишком короткий
        ]
        for password in weak_passwords:
            is_valid, _ = validate_user_password(password)
            self.assertFalse(is_valid, f"Слабый пароль {password} прошел валидацию")

        # Тест сильных паролей
        strong_passwords = [
            "StrongP@ssw0rd",
            "C0mpl3x!Pass",
            "Sup3r$3cur3"
        ]
        for password in strong_passwords:
            is_valid, message = validate_user_password(password)
            self.assertTrue(is_valid, f"Сильный пароль не прошел валидацию: {message}")

    def test_password_reset_flow(self):
        """
        Тест процесса сброса пароля.
        """
        # Тест для активного пользователя
        user, success = handle_password_reset(self.test_user)
        self.assertTrue(success)
        self.assertEqual(user, self.test_user)

        # Тест для неактивного пользователя
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@test.com',
            password='Test123!@#',
            is_active=False
        )
        user, success = handle_password_reset(inactive_user)
        self.assertFalse(success)

    def test_data_encryption(self):
        """
        Тест шифрования и расшифровки данных.
        """
        sensitive_data = "Секретные данные пользователя"
        encrypted = encrypt_user_data(sensitive_data)
        
        # Проверяем, что данные зашифрованы
        self.assertNotEqual(sensitive_data, encrypted)
        
        # Проверяем, что данные можно расшифровать
        decrypted = decrypt_user_data(encrypted)
        self.assertEqual(sensitive_data, decrypted)

        # Проверяем разные типы данных
        test_cases = [
            "Простой текст",
            "12345",
            "Special @#$% characters",
            "Русский текст",
            "Mixed 123 ## текст"
        ]
        
        for test_data in test_cases:
            encrypted = encrypt_user_data(test_data)
            decrypted = decrypt_user_data(encrypted)
            self.assertEqual(test_data, decrypted) 
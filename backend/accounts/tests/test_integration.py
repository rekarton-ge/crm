"""
Интеграционные тесты для проверки взаимодействия core и accounts.
"""

from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from core.tests.test_base import BaseTestCase
from core.utils.password_security import (
    generate_password,
    validate_password_strength,
    generate_password_reset_token
)
from accounts.models import User, UserSession, UserActivity
from accounts.utils.password_utils import (
    generate_user_password,
    validate_user_password,
    handle_password_reset
)
from rest_framework_simplejwt.tokens import AccessToken


class CoreAccountsIntegrationTest(BaseTestCase):
    """
    Тесты интеграции между core и accounts.
    """

    def setUp(self):
        super().setUp()
        # Создаем токен доступа для тестов
        self.access_token = str(AccessToken.for_user(self.test_user))

    def test_password_generation_compatibility(self):
        """
        Проверяет совместимость генерации паролей между core и accounts.
        """
        # Генерируем пароль через core
        core_password = generate_password(length=12, include_digits=True, include_special=True)
        
        # Проверяем его через accounts
        is_valid, _ = validate_user_password(core_password)
        self.assertTrue(is_valid)

        # Генерируем пароль через accounts
        accounts_password = generate_user_password()
        
        # Проверяем его через core
        is_valid, _ = validate_password_strength(accounts_password)
        self.assertTrue(is_valid)

    def test_password_reset_flow(self):
        """
        Проверяет процесс сброса пароля через core и accounts.
        """
        # Генерируем токен через core
        core_uid, core_token = generate_password_reset_token(self.test_user)
        
        # Проверяем его через accounts
        user, success = handle_password_reset(self.test_user)  # Распаковываем кортеж
        self.assertTrue(success)
        self.assertIsNotNone(user)
        
        # Проверяем, что токены работают в обоих случаях
        self.assertEqual(self.test_user.id, user.id)

    def test_session_activity_tracking(self):
        """
        Проверяет корректность отслеживания сессий и активности.
        """
        # Создаем сессию
        session = UserSession.objects.create(
            user=self.test_user,
            session_key=self.access_token,
            started_at=timezone.now()
        )

        # Запоминаем начальное количество активностей
        initial_count = UserActivity.objects.count()

        # Делаем один тестовый запрос
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.api_client.get('/api/accounts/users/me/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем активность
        activities = UserActivity.objects.filter(
            user=self.test_user,
            timestamp__gt=session.started_at  # Только активности после создания сессии
        )
        
        # Проверяем, что создалась ровно одна активность
        self.assertEqual(activities.count(), 1)
        
        # Проверяем тип активности
        activity = activities.first()
        self.assertEqual(activity.activity_type, 'view')
        self.assertEqual(activity.session, session)

    def test_authentication_middleware_chain(self):
        """
        Проверяет цепочку middleware аутентификации.
        """
        self.authenticate_client()
        
        # Создаем сессию с действительным токеном
        session = UserSession.objects.create(
            user=self.test_user,
            session_key=self.access_token,
            started_at=timezone.now()
        )
        
        # Устанавливаем токен для запроса
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Делаем запрос к защищенному ресурсу
        response = self.api_client.get('/api/accounts/users/me/profile/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем создание сессии
        self.assertTrue(
            UserSession.objects.filter(user=self.test_user).exists()
        )
        
        # Проверяем создание записи активности
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.test_user,
                activity_type='view'
            ).exists()
        )

    def test_security_utils_integration(self):
        """
        Проверяет интеграцию утилит безопасности.
        """
        from core.utils.security_utils import encrypt_data, decrypt_data
        from accounts.utils.password_utils import encrypt_user_data, decrypt_user_data
        
        # Тестовые данные
        test_data = "sensitive_user_info"
        
        # Шифруем через core
        core_encrypted = encrypt_data(test_data)
        # Расшифровываем через accounts
        accounts_decrypted = decrypt_user_data(core_encrypted)
        self.assertEqual(test_data, accounts_decrypted)
        
        # Шифруем через accounts
        accounts_encrypted = encrypt_user_data(test_data)
        # Расшифровываем через core
        core_decrypted = decrypt_data(accounts_encrypted)
        self.assertEqual(test_data, core_decrypted) 
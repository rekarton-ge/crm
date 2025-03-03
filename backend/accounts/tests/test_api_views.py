"""
Тесты для API views приложения accounts.
"""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from core.tests.test_base import BaseTestCase
from accounts.models import UserSession, LoginAttempt


class AuthViewsAPITest(BaseTestCase):
    """
    Тесты для представлений аутентификации API.
    """

    def setUp(self):
        super().setUp()
        self.login_url = reverse('accounts:login')
        self.register_url = reverse('accounts:register')
        self.sessions_url = reverse('accounts:sessions')
        self.end_all_sessions_url = reverse('accounts:end-all-sessions')
        
        self.valid_credentials = {
            'username': self.test_user.username,
            'password': 'test_password'
        }

    def test_login_success(self):
        """
        Тест успешной аутентификации.
        """
        response = self.api_client.post(self.login_url, self.valid_credentials)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем наличие токенов в ответе
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Проверяем создание сессии
        self.assertTrue(
            UserSession.objects.filter(
                user=self.test_user,
                ended_at__isnull=True
            ).exists()
        )
        
        # Проверяем запись о попытке входа
        self.assertTrue(
            LoginAttempt.objects.filter(
                username=self.test_user.username,
                was_successful=True
            ).exists()
        )

    def test_login_invalid_credentials(self):
        """
        Тест аутентификации с неверными учетными данными.
        """
        invalid_credentials = {
            'username': self.test_user.username,
            'password': 'wrong_password'
        }
        response = self.api_client.post(self.login_url, invalid_credentials)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Проверяем запись о неудачной попытке входа
        self.assertTrue(
            LoginAttempt.objects.filter(
                username=self.test_user.username,
                was_successful=False
            ).exists()
        )

    def test_login_inactive_user(self):
        """
        Тест аутентификации неактивного пользователя.
        """
        self.test_user.is_active = False
        self.test_user.save()
        
        response = self.api_client.post(self.login_url, self.valid_credentials)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_end_all_sessions(self):
        """
        Тест завершения всех сессий пользователя.
        """
        # Сначала входим в систему
        login_response = self.api_client.post(self.login_url, self.valid_credentials)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Завершаем все сессии
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        response = self.api_client.post(self.end_all_sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что все сессии завершены
        self.assertFalse(
            UserSession.objects.filter(
                user=self.test_user,
                ended_at__isnull=True
            ).exists()
        )

    def test_list_sessions(self):
        """
        Тест получения списка сессий пользователя.
        """
        # Входим в систему
        login_response = self.api_client.post(self.login_url, self.valid_credentials)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Получаем список сессий
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        response = self.api_client.get(self.sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем структуру ответа
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)  # Должна быть одна активная сессия 
"""
Тесты для views приложения accounts.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from core.tests.test_base import BaseTestCase
from accounts.models import UserSession
from django.utils import timezone
from rest_framework.test import APIClient
import time

User = get_user_model()


class AuthViewsTest(BaseTestCase):
    """
    Тесты для views аутентификации.
    """
    
    def setUp(self):
        super().setUp()
        self.login_data = {
            'username': self.test_user.username,
            'password': 'test_password'
        }
        self.register_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123'
        }

    def test_login_success(self):
        """
        Тест успешного входа в систему.
        """
        response = self.api_client.post(reverse('accounts:login'), self.login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_failure(self):
        """
        Тест неудачного входа в систему.
        """
        invalid_data = self.login_data.copy()
        invalid_data['password'] = 'wrong_password'
        response = self.api_client.post(reverse('accounts:login'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_success(self):
        """
        Тест успешной регистрации.
        """
        response = self.api_client.post(reverse('accounts:register'), self.register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.register_data['username']).exists())

    def test_register_validation(self):
        """
        Тест валидации данных при регистрации.
        """
        # Тест с несовпадающими паролями
        invalid_data = self.register_data.copy()
        invalid_data['password_confirm'] = 'different_password'
        response = self.api_client.post(reverse('accounts:register'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileViewsTest(BaseTestCase):
    """
    Тесты для views профиля пользователя.
    """

    def setUp(self):
        super().setUp()
        self.profile_url = reverse('accounts:profile')
        self.authenticate_client()

    def test_get_profile(self):
        """
        Тест получения профиля пользователя.
        """
        response = self.api_client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.test_user.username)
        self.assertEqual(response.data['email'], self.test_user.email)

    def test_update_profile(self):
        """
        Тест обновления профиля пользователя.
        """
        update_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@test.com'
        }
        response = self.api_client.patch(self.profile_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем обновление данных
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, update_data['first_name'])
        self.assertEqual(self.test_user.last_name, update_data['last_name'])
        self.assertEqual(self.test_user.email, update_data['email'])

    def test_profile_unauthorized(self):
        """
        Тест доступа к профилю без аутентификации.
        """
        self.api_client.credentials()  # Очищаем credentials
        response = self.api_client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserSessionViewsTest(BaseTestCase):
    """
    Тесты для views сессий пользователя.
    """

    def setUp(self):
        super().setUp()
        self.sessions_url = '/api/accounts/auth/sessions/'
        self.api_client = self.authenticate_client()

    def test_list_sessions(self):
        """
        Тест получения списка сессий пользователя.
        """
        # Выводим начальное состояние
        print("\nНачальное состояние:")
        for session in UserSession.objects.filter(user=self.test_user, ended_at__isnull=True):
            print(f"ID: {session.id}, Key: {session.session_key}, IP: {session.ip_address}")

        # Завершаем все текущие сессии пользователя
        UserSession.objects.filter(user=self.test_user).update(ended_at=timezone.now())

        print("\nПосле завершения всех сессий:")
        for session in UserSession.objects.filter(user=self.test_user, ended_at__isnull=True):
            print(f"ID: {session.id}, Key: {session.session_key}, IP: {session.ip_address}")

        # Создаем две тестовые сессии
        session1 = UserSession.objects.create(
            user=self.test_user,
            session_key=f"test_session_1_{time.time()}",
            ip_address="127.0.0.1",
            user_agent="Test Agent 1",
            device_type="desktop"
        )
        session2 = UserSession.objects.create(
            user=self.test_user,
            session_key=f"test_session_2_{time.time()}",
            ip_address="127.0.0.2",
            user_agent="Test Agent 2",
            device_type="mobile"
        )

        print("\nПосле создания тестовых сессий:")
        for session in UserSession.objects.filter(user=self.test_user, ended_at__isnull=True):
            print(f"ID: {session.id}, Key: {session.session_key}, IP: {session.ip_address}")

        # Получаем список сессий через API
        response = self.api_client.get(self.sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        print("\nФинальное состояние:")
        for session in UserSession.objects.filter(user=self.test_user, ended_at__isnull=True):
            print(f"ID: {session.id}, Key: {session.session_key}, IP: {session.ip_address}")

        print("\nОтвет API:")
        print(f"Content-Type: {response['Content-Type']}")
        print(f"Raw response: {response.content.decode()}")
        
        response_data = response.json()
        print(f"\nТип response_data: {type(response_data)}")
        print(f"Содержимое response_data: {response_data}")

        # Проверяем количество активных сессий
        self.assertEqual(response_data['count'], 2)
        self.assertEqual(len(response_data['results']), 2)

        # Проверяем, что возвращаются правильные сессии
        session_ids = {session['id'] for session in response_data['results']}
        self.assertIn(session1.id, session_ids)
        self.assertIn(session2.id, session_ids)

    def test_end_session(self):
        """
        Тест завершения сессии.
        """
        # Создаем тестовую сессию
        session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_1',
            ip_address='127.0.0.1'
        )
        
        response = self.api_client.delete(f"{self.sessions_url}{session.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что сессия завершена
        session.refresh_from_db()
        self.assertIsNotNone(session.ended_at)

    def test_end_all_sessions(self):
        """
        Тест завершения всех сессий пользователя.
        """
        response = self.api_client.post(f"{self.sessions_url}end-all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что все сессии завершены
        active_sessions = UserSession.get_active_sessions(self.test_user)
        self.assertEqual(active_sessions.count(), 0)

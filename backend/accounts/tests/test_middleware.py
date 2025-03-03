"""
Тесты для middleware приложения accounts.
"""

from django.urls import reverse
from django.utils import timezone
from core.tests.test_base import BaseTestCase
from accounts.models import UserSession, UserActivity


class JWTAuthenticationMiddlewareTest(BaseTestCase):
    """
    Тесты для JWTAuthenticationMiddleware.
    """

    def setUp(self):
        super().setUp()
        self.login_url = '/api/accounts/auth/login/'
        self.protected_url = '/api/accounts/users/me/profile/'

    def test_authentication_success(self):
        """
        Тест успешной аутентификации через JWT токен.
        """
        self.authenticate_client()
        response = self.api_client.get(self.protected_url)
        self.assertEqual(response.status_code, 200)

    def test_authentication_failure_invalid_token(self):
        """
        Тест неудачной аутентификации с неверным токеном.
        """
        self.api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.api_client.get(self.protected_url)
        self.assertEqual(response.status_code, 401)

    def test_authentication_failure_no_token(self):
        """
        Тест неудачной аутентификации без токена.
        """
        response = self.api_client.get(self.protected_url)
        self.assertEqual(response.status_code, 401)

    def test_session_update(self):
        """
        Тест обновления сессии пользователя.
        """
        self.authenticate_client()
        
        # Создаем сессию
        initial_time = timezone.now()
        session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key',  # Используем фиксированный короткий ключ для теста
            started_at=initial_time
        )

        # Делаем запрос
        self.api_client.get(self.protected_url)
        
        # Проверяем обновление времени последней активности
        session.refresh_from_db()
        self.assertGreater(session.last_activity, initial_time)


class UserActivityMiddlewareTest(BaseTestCase):
    """
    Тесты для UserActivityMiddleware.
    """

    def setUp(self):
        super().setUp()
        self.test_url = '/api/accounts/users/me/profile/'

    def test_activity_logging(self):
        """
        Тест логирования активности пользователя.
        """
        self.authenticate_client()
        
        # Проверяем начальное количество записей
        initial_count = UserActivity.objects.count()
        
        # Делаем запрос
        response = self.api_client.get(self.test_url)
        
        # Проверяем создание записи об активности
        self.assertEqual(UserActivity.objects.count(), initial_count + 1)
        
        activity = UserActivity.objects.latest('id')
        self.assertEqual(activity.user, self.test_user)
        self.assertEqual(activity.activity_type, 'view')
        self.assertIn(self.test_url, activity.description)

    def test_activity_logging_excluded_path(self):
        """
        Тест отсутствия логирования для исключенных путей.
        """
        self.authenticate_client()
        
        initial_count = UserActivity.objects.count()
        
        # Делаем запрос к исключенному пути
        response = self.api_client.post('/api/auth/token/refresh/', 
                                      {'refresh': self.get_tokens_for_user(self.test_user)['refresh']})
        
        # Проверяем, что запись об активности не создана
        self.assertEqual(UserActivity.objects.count(), initial_count)

    def test_activity_logging_unauthenticated(self):
        """
        Тест отсутствия логирования для неаутентифицированных пользователей.
        """
        initial_count = UserActivity.objects.count()
        
        # Делаем запрос без аутентификации
        response = self.api_client.get(self.test_url)
        
        # Проверяем, что запись об активности не создана
        self.assertEqual(UserActivity.objects.count(), initial_count) 
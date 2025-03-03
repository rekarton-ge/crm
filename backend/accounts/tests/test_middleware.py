"""
Тесты для middleware приложения accounts.
"""

from django.urls import reverse
from django.utils import timezone
from core.tests.test_base import BaseTestCase
from accounts.models import UserSession, UserActivity
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from accounts.middleware.auth_middleware import JWTAuthenticationMiddleware, UserActivityMiddleware
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class JWTAuthenticationMiddlewareTest(TestCase):
    """
    Тесты для JWTAuthenticationMiddleware.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = AnonymousUser()
        
        # Создаем тестового пользователя
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Генерируем токен
        refresh = RefreshToken.for_user(self.test_user)
        self.access_token = str(refresh.access_token)
        
        self.middleware = JWTAuthenticationMiddleware(lambda x: x)
        self.request.META['HTTP_AUTHORIZATION'] = f'Bearer {self.access_token}'

    def test_authentication_success(self):
        """
        Тест успешной аутентификации через JWT токен.
        """
        response = self.middleware(self.request)
        self.assertEqual(response.user, self.test_user)
        session = UserSession.objects.filter(user=self.test_user).first()
        self.assertIsNotNone(session)

    def test_authentication_failure_no_token(self):
        """
        Тест неудачной аутентификации без токена.
        """
        self.request.META.pop('HTTP_AUTHORIZATION', None)
        response = self.middleware(self.request)
        self.assertTrue(response.user.is_anonymous)

    def test_authentication_failure_invalid_token(self):
        """
        Тест неудачной аутентификации с неверным токеном.
        """
        self.request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid_token'
        response = self.middleware(self.request)
        self.assertTrue(response.user.is_anonymous)

    def test_session_update(self):
        """
        Тест обновления сессии пользователя.
        """
        response = self.middleware(self.request)
        session = UserSession.objects.filter(user=self.test_user).first()
        self.assertIsNotNone(session)
        old_last_activity = session.last_activity
        response = self.middleware(self.request)
        session.refresh_from_db()
        self.assertGreater(session.last_activity, old_last_activity)

    def test_excluded_url_static(self):
        """
        Тест исключения статических URL.
        """
        request = self.factory.get('/static/test.css')
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertTrue(response.user.is_anonymous)

    def test_excluded_url_media(self):
        """
        Тест исключения медиа URL.
        """
        request = self.factory.get('/media/test.jpg')
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertTrue(response.user.is_anonymous)

    def test_excluded_url_api(self):
        """
        Тест исключения API URL.
        """
        request = self.factory.get('/api/accounts/auth/sessions/')
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertTrue(response.user.is_anonymous)

    def test_get_client_ip_with_x_forwarded_for(self):
        """
        Тест получения IP-адреса с X-Forwarded-For.
        """
        self.request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 10.0.0.2'
        response = self.middleware(self.request)
        session = UserSession.objects.filter(user=self.test_user).first()
        self.assertEqual(session.ip_address, '10.0.0.1')

    def test_get_client_ip_without_x_forwarded_for(self):
        """
        Тест получения IP-адреса без X-Forwarded-For.
        """
        self.request.META['REMOTE_ADDR'] = '192.168.1.1'
        response = self.middleware(self.request)
        session = UserSession.objects.filter(user=self.test_user).first()
        self.assertEqual(session.ip_address, '192.168.1.1')

    def test_inactive_user(self):
        """
        Тест аутентификации неактивного пользователя.
        """
        self.test_user.is_active = False
        self.test_user.save()
        response = self.middleware(self.request)
        self.assertTrue(response.user.is_anonymous)

    def test_session_update_exception(self):
        """
        Тест обработки исключений при обновлении сессии.
        """
        session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session',
            ip_address='127.0.0.1',
            user_agent='Test User Agent',
            device_type='other'
        )
        response = self.middleware(self.request)
        self.assertIsNotNone(response)

    def test_multiple_sessions_cleanup(self):
        """
        Тест очистки множественных сессий при входе.
        """
        # Создаем несколько сессий
        UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_1',
            ip_address='127.0.0.1',
            user_agent='Test User Agent 1'
        )
        UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_2',
            ip_address='127.0.0.2',
            user_agent='Test User Agent 2'
        )
        
        # Делаем новый запрос с новым токеном
        refresh = RefreshToken.for_user(self.test_user)
        self.request.META['HTTP_AUTHORIZATION'] = f'Bearer {str(refresh.access_token)}'
        
        response = self.middleware(self.request)
        active_sessions = UserSession.objects.filter(user=self.test_user, ended_at=None)
        self.assertEqual(active_sessions.count(), 1)


class UserActivityMiddlewareTest(TestCase):
    """
    Тесты для UserActivityMiddleware.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        # Создаем тестового пользователя
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Генерируем токен
        refresh = RefreshToken.for_user(self.test_user)
        self.access_token = str(refresh.access_token)
        
        self.middleware = UserActivityMiddleware(lambda x: HttpResponse())
        self.request.user = self.test_user
        self.request.META['HTTP_AUTHORIZATION'] = f'Bearer {self.access_token}'
        
        # Создаем сессию
        self.session = UserSession.objects.create(
            user=self.test_user,
            session_key=self.access_token,
            ip_address='127.0.0.1',
            user_agent='Test User Agent',
            device_type='desktop'
        )
        self.request.user_session = self.session

    def test_activity_logging(self):
        """
        Тест логирования активности пользователя.
        """
        response = HttpResponse()
        response.status_code = 200
        self.request.path = '/api/test/'
        self.middleware.__call__(self.request)
        self.assertTrue(
            UserActivity.objects.filter(user=self.test_user).exists()
        )

    def test_activity_logging_excluded_path(self):
        """
        Тест отсутствия логирования для исключенных путей.
        """
        self.request.path = '/api/auth/test/'
        initial_count = UserActivity.objects.count()
        self.middleware.__call__(self.request)
        self.assertEqual(UserActivity.objects.count(), initial_count)

    def test_activity_logging_unauthenticated(self):
        """
        Тест отсутствия логирования для неаутентифицированных пользователей.
        """
        self.request.user = AnonymousUser()
        initial_count = UserActivity.objects.count()
        self.middleware.__call__(self.request)
        self.assertEqual(UserActivity.objects.count(), initial_count)

    def test_activity_logging_error_response(self):
        """
        Тест отсутствия логирования для ответов с ошибками.
        """
        initial_count = UserActivity.objects.count()
        self.middleware = UserActivityMiddleware(lambda x: HttpResponse(status=500))
        self.request.path = '/api/test/'
        self.middleware.__call__(self.request)
        self.assertEqual(UserActivity.objects.count(), initial_count)

    def test_activity_logging_with_session(self):
        """
        Тест логирования активности с привязкой к сессии.
        """
        self.request.path = '/api/test/'
        self.middleware.__call__(self.request)
        activity = UserActivity.objects.filter(
            user=self.test_user,
            session=self.session
        ).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.session, self.session)

    def test_activity_logging_exception(self):
        """
        Тест обработки исключений при логировании активности.
        """
        def bad_response(request):
            response = HttpResponse()
            response.status_code = 200
            raise Exception("Test exception")
            return response

        middleware = UserActivityMiddleware(bad_response)
        with self.assertRaises(Exception):
            middleware(self.request)
        # Проверяем, что активность не была залогирована
        self.assertFalse(
            UserActivity.objects.filter(
                user=self.test_user,
                description__contains="Test exception"
            ).exists()
        ) 
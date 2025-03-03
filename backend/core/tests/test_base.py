"""
Базовые классы для тестирования.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Базовый класс для всех тестов.
    """
    
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        
        # Создаем тестового пользователя
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test_password'
        )
        
        # Создаем тестового админа
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin_password_123'
        )

    def get_tokens_for_user(self, user):
        """
        Получает JWT токены для пользователя.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def authenticate_client(self, user=None):
        """
        Аутентифицирует API клиент для пользователя.
        """
        if user is None:
            user = self.test_user
        
        tokens = self.get_tokens_for_user(user)
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        # Создаем тестовую сессию для токена
        from accounts.models import UserSession
        from django.utils import timezone
        
        # Проверяем наличие активной сессии с этим токеном
        session = UserSession.objects.filter(
            user=user,
            session_key=tokens["access"],
            ended_at__isnull=True
        ).first()
        
        if not session:
            # Создаем новую сессию
            UserSession.objects.create(
                user=user,
                session_key=tokens["access"],
                ip_address='127.0.0.1',
                started_at=timezone.now(),
                last_activity=timezone.now(),
                user_agent='Test User Agent'
            )
        
        return self.api_client 
"""
Тесты для моделей приложения accounts.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from accounts.models import UserSession, LoginAttempt, UserActivity
from core.tests.test_base import BaseTestCase
import time

User = get_user_model()


class UserSessionTest(BaseTestCase):
    """
    Тесты для модели UserSession.
    """
    
    def setUp(self):
        super().setUp()
        self.session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key',
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            device_type='desktop'
        )

    def test_session_creation(self):
        """
        Тест создания сессии.
        """
        self.assertIsNotNone(self.session.started_at)
        self.assertIsNone(self.session.ended_at)
        self.assertTrue(self.session.is_active())

    def test_session_end(self):
        """
        Тест завершения сессии.
        """
        self.session.end_session()
        self.assertIsNotNone(self.session.ended_at)
        self.assertFalse(self.session.is_active())

    def test_get_active_sessions(self):
        """
        Тест получения активных сессий.
        """
        # Создаем дополнительную активную сессию
        UserSession.objects.create(
            user=self.test_user,
            session_key='another_session_key',
            ip_address='127.0.0.2'
        )
        
        # Создаем завершенную сессию
        ended_session = UserSession.objects.create(
            user=self.test_user,
            session_key='ended_session_key',
            ip_address='127.0.0.3'
        )
        ended_session.end_session()
        
        active_sessions = UserSession.get_active_sessions(self.test_user)
        self.assertEqual(active_sessions.count(), 2)


class LoginAttemptTest(BaseTestCase):
    """
    Тесты для модели LoginAttempt.
    """

    def test_successful_login_attempt(self):
        """
        Тест успешной попытки входа.
        """
        attempt = LoginAttempt.log_login_attempt(
            username=self.test_user.username,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            was_successful=True
        )
        
        self.assertTrue(attempt.was_successful)
        self.assertEqual(attempt.username, self.test_user.username)
        self.assertEqual(attempt.failure_reason, '')

    def test_failed_login_attempt(self):
        """
        Тест неудачной попытки входа.
        """
        failure_reason = 'Invalid password'
        attempt = LoginAttempt.log_login_attempt(
            username='nonexistent_user',
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            was_successful=False,
            failure_reason=failure_reason
        )
        
        self.assertFalse(attempt.was_successful)
        self.assertEqual(attempt.failure_reason, failure_reason)


class UserActivityTest(BaseTestCase):
    """
    Тесты для модели UserActivity.
    """

    def setUp(self):
        super().setUp()
        self.session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key'
        )

    def test_activity_logging(self):
        """
        Тест логирования активности.
        """
        activity = UserActivity.log_activity(
            user=self.test_user,
            activity_type='view',
            description='Просмотр профиля',
            session=self.session,
            ip_address='127.0.0.1',
            object_type='Profile',
            object_id='1'
        )
        
        self.assertEqual(activity.user, self.test_user)
        self.assertEqual(activity.activity_type, 'view')
        self.assertEqual(activity.session, self.session)

    def test_activity_types(self):
        """
        Тест различных типов активности.
        """
        activity_types = ['login', 'logout', 'create', 'update', 'delete']
        
        for activity_type in activity_types:
            activity = UserActivity.log_activity(
                user=self.test_user,
                activity_type=activity_type,
                description=f'Test {activity_type} activity',
                session=self.session
            )
            self.assertEqual(activity.activity_type, activity_type)

    def test_activity_ordering(self):
        """
        Тест сортировки активностей по времени.
        """
        # Очищаем все предыдущие активности
        UserActivity.objects.all().delete()
        
        # Создаем несколько активностей с небольшой задержкой
        activities = []
        for i in range(3):
            activity = UserActivity.log_activity(
                user=self.test_user,
                activity_type='view',
                description=f'Activity {i}',
                session=self.session
            )
            activities.append(activity)
            time.sleep(0.1)  # Добавляем небольшую задержку между созданием активностей
        
        # Получаем активности из базы данных
        db_activities = list(UserActivity.objects.filter(
            user=self.test_user,
            activity_type='view'
        ).order_by('-timestamp'))
        
        # Проверяем, что активности отсортированы от новых к старым
        for i in range(len(activities)):
            self.assertEqual(db_activities[i].id, activities[-(i+1)].id)

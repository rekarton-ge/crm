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
            user_agent='Test User Agent',
            device_type='desktop',
            location='Test Location'
        )

    def test_session_creation(self):
        """
        Тест создания сессии.
        """
        self.assertEqual(self.session.user, self.test_user)
        self.assertEqual(self.session.session_key, 'test_session_key')
        self.assertEqual(self.session.ip_address, '127.0.0.1')
        self.assertEqual(self.session.user_agent, 'Test User Agent')
        self.assertEqual(self.session.device_type, 'desktop')
        self.assertEqual(self.session.location, 'Test Location')
        self.assertIsNotNone(self.session.started_at)
        self.assertIsNotNone(self.session.last_activity)
        self.assertIsNone(self.session.ended_at)

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
        # Создаем дополнительные сессии
        session2 = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key_2',
            ip_address='127.0.0.2',
            user_agent='Test User Agent 2',
            device_type='other'
        )
        session3 = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key_3',
            ip_address='127.0.0.3',
            user_agent='Test User Agent 3',
            device_type='other'
        )
        session3.end_session()  # Завершаем одну сессию

        active_sessions = UserSession.get_active_sessions(self.test_user)
        self.assertEqual(active_sessions.count(), 2)
        self.assertIn(self.session, active_sessions)
        self.assertIn(session2, active_sessions)
        self.assertNotIn(session3, active_sessions)

    def test_is_active(self):
        """
        Тест проверки активности сессии.
        """
        self.assertTrue(self.session.is_active())
        self.session.end_session()
        self.assertFalse(self.session.is_active())

    def test_update_activity(self):
        """
        Тест обновления времени последней активности.
        """
        old_last_activity = self.session.last_activity
        self.session.update_activity()
        self.assertGreater(self.session.last_activity, old_last_activity)

    def test_get_device_info(self):
        """
        Тест получения информации об устройстве.
        """
        device_info = self.session.get_device_info()
        self.assertEqual(device_info['device_type'], 'desktop')
        self.assertEqual(device_info['user_agent'], 'Test User Agent')
        self.assertEqual(device_info['location'], 'Test Location')

    def test_get_session_duration(self):
        """
        Тест получения длительности сессии.
        """
        # Для активной сессии
        duration = self.session.get_session_duration()
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration.total_seconds(), 0)

        # Для завершенной сессии
        self.session.end_session()
        duration = self.session.get_session_duration()
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration.total_seconds(), 0)

    def test_end_all_user_sessions(self):
        """
        Тест завершения всех сессий пользователя.
        """
        # Создаем дополнительные сессии
        UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key_2',
            ip_address='127.0.0.2',
            user_agent='Test User Agent 2',
            device_type='other'
        )
        UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key_3',
            ip_address='127.0.0.3',
            user_agent='Test User Agent 3',
            device_type='other'
        )

        # Проверяем, что у пользователя есть активные сессии
        self.assertEqual(UserSession.get_active_sessions(self.test_user).count(), 3)

        # Завершаем все сессии
        UserSession.end_all_user_sessions(self.test_user)

        # Проверяем, что все сессии завершены
        self.assertEqual(UserSession.get_active_sessions(self.test_user).count(), 0)
        for session in UserSession.objects.filter(user=self.test_user):
            self.assertIsNotNone(session.ended_at)

    def test_get_last_active_session(self):
        """
        Тест получения последней активной сессии.
        """
        # Создаем дополнительную сессию с более поздним временем активности
        later_session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session_key_2',
            ip_address='127.0.0.2',
            user_agent='Test User Agent 2',
            device_type='other'
        )

        last_session = UserSession.get_last_active_session(self.test_user)
        self.assertEqual(last_session, later_session)

        # Завершаем последнюю сессию
        later_session.end_session()
        last_session = UserSession.get_last_active_session(self.test_user)
        self.assertEqual(last_session, self.session)


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
            session_key='test_session_key',
            ip_address='127.0.0.1',
            user_agent='Test User Agent',
            device_type='desktop'
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

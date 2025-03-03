"""
Тесты для serializers приложения accounts.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserSessionSerializer,
    UserActivitySerializer,
    LoginSerializer,
    RegisterSerializer
)
from accounts.models import UserSession, UserActivity
from core.tests.test_base import BaseTestCase
from rest_framework.exceptions import ValidationError

User = get_user_model()


class UserSerializerTest(BaseTestCase):
    """
    Тесты для UserSerializer.
    """

    def test_user_serialization(self):
        """
        Тест сериализации пользователя.
        """
        serializer = UserSerializer(self.test_user)
        data = serializer.data
        
        self.assertEqual(data['username'], self.test_user.username)
        self.assertEqual(data['email'], self.test_user.email)
        self.assertNotIn('password', data)

    def test_user_deserialization(self):
        """
        Тест десериализации пользователя.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'StrongP@ss123'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class UserProfileSerializerTest(BaseTestCase):
    """
    Тесты для UserProfileSerializer.
    """

    def test_profile_serialization(self):
        """
        Тест сериализации профиля.
        """
        self.test_user.first_name = 'Test'
        self.test_user.last_name = 'User'
        self.test_user.save()

        serializer = UserProfileSerializer(self.test_user)
        data = serializer.data

        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['email'], self.test_user.email)

    def test_profile_update(self):
        """
        Тест обновления профиля.
        """
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com'
        }
        serializer = UserProfileSerializer(self.test_user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, update_data['first_name'])
        self.assertEqual(updated_user.last_name, update_data['last_name'])
        self.assertEqual(updated_user.email, update_data['email'])


class LoginSerializerTest(BaseTestCase):
    """
    Тесты для LoginSerializer.
    """

    def test_valid_credentials(self):
        """
        Тест валидации корректных учетных данных.
        """
        data = {
            'username': self.test_user.username,
            'password': 'test_password'
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['user'], self.test_user)

    def test_invalid_credentials(self):
        """
        Тест валидации некорректных учетных данных.
        """
        data = {
            'username': self.test_user.username,
            'password': 'wrong_password'
        }
        serializer = LoginSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class RegisterSerializerTest(BaseTestCase):
    """
    Тесты для RegisterSerializer.
    """

    def test_valid_registration(self):
        """
        Тест валидной регистрации.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'StrongP@ss123'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_validation(self):
        """
        Тест валидации паролей.
        """
        # Тест несовпадающих паролей
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'StrongP@ss123',
            'password_confirm': 'DifferentP@ss123'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

        # Тест слабого пароля
        data['password'] = data['password_confirm'] = 'weak'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class UserSessionSerializerTest(BaseTestCase):
    """
    Тесты для UserSessionSerializer.
    """

    def setUp(self):
        super().setUp()
        self.session = UserSession.objects.create(
            user=self.test_user,
            session_key='test_session',
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            device_type='desktop'
        )

    def test_session_serialization(self):
        """
        Тест сериализации сессии.
        """
        serializer = UserSessionSerializer(self.session)
        data = serializer.data

        self.assertEqual(data['ip_address'], '127.0.0.1')
        self.assertEqual(data['device_type'], 'desktop')
        self.assertEqual(data['user_agent'], 'Test Browser')
        self.assertIsNotNone(data['started_at'])


class UserActivitySerializerTest(BaseTestCase):
    """
    Тесты для UserActivitySerializer.
    """

    def setUp(self):
        super().setUp()
        self.activity = UserActivity.objects.create(
            user=self.test_user,
            activity_type='view',
            description='Test activity',
            ip_address='127.0.0.1'
        )

    def test_activity_serialization(self):
        """
        Тест сериализации активности.
        """
        serializer = UserActivitySerializer(self.activity)
        data = serializer.data

        self.assertEqual(data['activity_type'], 'view')
        self.assertEqual(data['description'], 'Test activity')
        self.assertEqual(data['ip_address'], '127.0.0.1')
        self.assertIsNotNone(data['timestamp']) 
"""
Тесты для моделей приложения Core.

Этот модуль содержит тесты для моделей приложения Core.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from core.models import (
    Tag, TaggedItem, Setting, Category, AuditLog, LoginAttempt,
    TemplateCategory, Template, TemplateVersion, NotificationChannel,
    NotificationType, Notification, UserNotificationPreference,
    SystemSetting, UserSetting, Theme
)

User = get_user_model()


class TagModelTest(TestCase):
    """
    Тесты для модели Tag.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.tag = Tag.objects.create(
            name='Test Tag',
            slug='test-tag',
            description='Test tag description',
            color='#FF0000',
            created_by=self.user
        )
    
    def test_tag_creation(self):
        """
        Тест создания тега.
        """
        self.assertEqual(self.tag.name, 'Test Tag')
        self.assertEqual(self.tag.slug, 'test-tag')
        self.assertEqual(self.tag.description, 'Test tag description')
        self.assertEqual(self.tag.color, '#FF0000')
        self.assertEqual(self.tag.created_by, self.user)
    
    def test_tag_str(self):
        """
        Тест строкового представления тега.
        """
        self.assertEqual(str(self.tag), 'Test Tag')


class CategoryModelTest(TestCase):
    """
    Тесты для модели Category.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.parent_category = Category.objects.create(
            name='Parent Category',
            slug='parent-category',
            description='Parent category description',
            created_by=self.user
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description',
            parent=self.parent_category,
            created_by=self.user
        )
    
    def test_category_creation(self):
        """
        Тест создания категории.
        """
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(self.category.description, 'Test category description')
        self.assertEqual(self.category.parent, self.parent_category)
        self.assertEqual(self.category.created_by, self.user)
    
    def test_category_str(self):
        """
        Тест строкового представления категории.
        """
        self.assertEqual(str(self.category), 'Test Category')
    
    def test_category_hierarchy(self):
        """
        Тест иерархии категорий.
        """
        self.assertEqual(self.category.parent, self.parent_category)
        self.assertIn(self.category, self.parent_category.children.all())


class SettingModelTest(TestCase):
    """
    Тесты для модели Setting.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.system_setting = SystemSetting.objects.create(
            key='system.test_key',
            value='test_value',
            description='Test system setting',
            created_by=self.user
        )
        
        self.user_setting = UserSetting.objects.create(
            key='user.test_key',
            value='test_value',
            user=self.user,
            created_by=self.user
        )
    
    def test_system_setting_creation(self):
        """
        Тест создания системной настройки.
        """
        self.assertEqual(self.system_setting.key, 'system.test_key')
        self.assertEqual(self.system_setting.value, 'test_value')
        self.assertEqual(self.system_setting.description, 'Test system setting')
        self.assertEqual(self.system_setting.created_by, self.user)
    
    def test_user_setting_creation(self):
        """
        Тест создания пользовательской настройки.
        """
        self.assertEqual(self.user_setting.key, 'user.test_key')
        self.assertEqual(self.user_setting.value, 'test_value')
        self.assertEqual(self.user_setting.user, self.user)
        self.assertEqual(self.user_setting.created_by, self.user)
    
    def test_setting_str(self):
        """
        Тест строкового представления настройки.
        """
        self.assertEqual(str(self.system_setting), 'system.test_key (Общие)')
        self.assertEqual(str(self.user_setting), 'testuser - user.test_key')


class AuditLogModelTest(TestCase):
    """
    Тесты для модели AuditLog.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        user_content_type = ContentType.objects.get_for_model(User)
        
        self.audit_log = AuditLog.objects.create(
            action='create',
            content_type=user_content_type,
            object_id='1',
            object_repr='testuser',
            data={'username': 'testuser', 'email': 'test@example.com'},
            user=self.user,
            ip_address='127.0.0.1'
        )
    
    def test_audit_log_creation(self):
        """
        Тест создания записи аудита.
        """
        self.assertEqual(self.audit_log.action, 'create')
        self.assertEqual(self.audit_log.content_type.model, 'user')
        self.assertEqual(self.audit_log.object_id, '1')
        self.assertEqual(self.audit_log.object_repr, 'testuser')
        self.assertEqual(self.audit_log.data, {'username': 'testuser', 'email': 'test@example.com'})
        self.assertEqual(self.audit_log.user, self.user)
        self.assertEqual(self.audit_log.ip_address, '127.0.0.1')
    
    def test_audit_log_str(self):
        """
        Тест строкового представления записи аудита.
        """
        expected = f"Создание - {self.user} - {self.audit_log.created_at}"
        self.assertEqual(str(self.audit_log), expected)

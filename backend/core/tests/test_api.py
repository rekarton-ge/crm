"""
Тесты для API приложения Core.

Этот модуль содержит тесты для API приложения Core.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import (
    Tag, Category, Setting, SystemSetting, UserSetting,
    NotificationType, NotificationChannel, Template, TemplateCategory
)

User = get_user_model()


class TagAPITest(APITestCase):
    """
    Тесты для API тегов.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.client = APIClient()
        
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создаем администратора
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True,
            is_superuser=True
        )
        
        # Создаем теги
        self.tag1 = Tag.objects.create(
            name='Test Tag 1',
            slug='test-tag-1',
            description='Test tag 1 description',
            color='#FF0000',
            created_by=self.user
        )
        
        self.tag2 = Tag.objects.create(
            name='Test Tag 2',
            slug='test-tag-2',
            description='Test tag 2 description',
            color='#00FF00',
            created_by=self.user
        )
        
        # URL для API тегов
        self.url = reverse('core:api:tag-list')
    
    def test_get_tags_unauthenticated(self):
        """
        Тест получения списка тегов без аутентификации.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_tags_authenticated(self):
        """
        Тест получения списка тегов с аутентификацией.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_tag_unauthenticated(self):
        """
        Тест создания тега без аутентификации.
        """
        data = {
            'name': 'New Tag',
            'slug': 'new-tag',
            'description': 'New tag description',
            'color': '#0000FF'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_tag_authenticated(self):
        """
        Тест создания тега с аутентификацией.
        """
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'New Tag',
            'slug': 'new-tag',
            'description': 'New tag description',
            'color': '#FF0000'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 3)
        self.assertEqual(Tag.objects.get(slug='new-tag').name, 'New Tag')
    
    def test_update_tag(self):
        """
        Тест обновления тега.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:tag-detail', args=[self.tag1.id])
        data = {
            'name': 'Updated Tag',
            'description': 'Updated tag description'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag1.refresh_from_db()
        self.assertEqual(self.tag1.name, 'Updated Tag')
        self.assertEqual(self.tag1.description, 'Updated tag description')
    
    def test_delete_tag(self):
        """
        Тест удаления тега.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:tag-detail', args=[self.tag1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что тег помечен как удаленный, а не удален из базы данных
        self.tag1.refresh_from_db()
        self.assertTrue(self.tag1.is_deleted)
        self.assertIsNotNone(self.tag1.deleted_at)
        
        # Проверяем, что общее количество тегов в базе данных не изменилось
        self.assertEqual(Tag.objects.count(), 2)
        
        # Проверяем, что количество неудаленных тегов уменьшилось
        self.assertEqual(Tag.objects.filter(is_deleted=False).count(), 1)


class CategoryAPITest(APITestCase):
    """
    Тесты для API категорий.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.client = APIClient()
        
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создаем администратора
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True,
            is_superuser=True
        )
        
        # Создаем категории
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
        
        # URL для API категорий
        self.url = reverse('core:api:category-list')
    
    def test_get_categories_unauthenticated(self):
        """
        Тест получения списка категорий без аутентификации.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_categories_authenticated(self):
        """
        Тест получения списка категорий с аутентификацией.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_category_unauthenticated(self):
        """
        Тест создания категории без аутентификации.
        """
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'New category description'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_category_authenticated(self):
        """
        Тест создания категории с аутентификацией.
        """
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'New category description',
            'parent': self.parent_category.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Category.objects.get(slug='new-category').name, 'New Category')
    
    def test_update_category(self):
        """
        Тест обновления категории.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:category-detail', args=[self.category.id])
        data = {
            'name': 'Updated Category',
            'description': 'Updated category description'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Category')
        self.assertEqual(self.category.description, 'Updated category description')
    
    def test_delete_category(self):
        """
        Тест удаления категории.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что категория помечена как удаленная, а не удалена из базы данных
        self.category.refresh_from_db()
        self.assertTrue(self.category.is_deleted)
        self.assertIsNotNone(self.category.deleted_at)
        
        # Проверяем, что общее количество категорий в базе данных не изменилось
        self.assertEqual(Category.objects.count(), 2)
        
        # Проверяем, что количество неудаленных категорий уменьшилось
        self.assertEqual(Category.objects.filter(is_deleted=False).count(), 1)


class SettingAPITest(APITestCase):
    """
    Тесты для API настроек.
    """
    
    def setUp(self):
        """
        Настройка тестов.
        """
        self.client = APIClient()
        
        # Создаем пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создаем администратора
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True,
            is_superuser=True
        )
        
        # Создаем настройки
        self.system_setting = Setting.objects.create(
            key='system.test_key',
            value='test_value',
            description='Test system setting',
            created_by=self.admin
        )
        
        self.user_setting = Setting.objects.create(
            key='user.test_key',
            value='test_value',
            created_by=self.user
        )
        
        # URL для API настроек
        self.url = reverse('core:api:setting-list')
    
    def test_get_settings_unauthenticated(self):
        """
        Тест получения списка настроек без аутентификации.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_settings_authenticated(self):
        """
        Тест получения списка настроек с аутентификацией.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Пользователь должен видеть все настройки
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_setting_unauthenticated(self):
        """
        Тест создания настройки без аутентификации.
        """
        data = {
            'key': 'new.test_key',
            'value': 'new_value',
            'description': 'New setting'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_user_setting(self):
        """
        Тест создания пользовательской настройки.
        """
        self.client.force_authenticate(user=self.admin)
        data = {
            'key': 'user_setting',
            'value': {'test': 'value'},
            'description': 'User setting description'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Setting.objects.count(), 3)
        self.assertEqual(Setting.objects.get(key='user_setting').value, {'test': 'value'})
    
    def test_create_system_setting_as_user(self):
        """
        Тест создания системной настройки обычным пользователем.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'key': 'system.new_key',
            'value': 'new_value',
            'description': 'New system setting'
        }
        response = self.client.post(self.url, data)
        # Обычный пользователь не должен иметь возможности создавать системные настройки
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_system_setting_as_admin(self):
        """
        Тест создания системной настройки администратором.
        """
        self.client.force_authenticate(user=self.admin)
        data = {
            'key': 'system_setting_2',
            'value': {'test': 'value'},
            'description': 'System setting description',
            'is_public': True
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Setting.objects.count(), 3)
        self.assertEqual(Setting.objects.get(key='system_setting_2').value, {'test': 'value'})
    
    def test_update_user_setting(self):
        """
        Тест обновления пользовательской настройки.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:setting-detail', args=[self.user_setting.id])
        data = {
            'value': {'updated': 'value'},
            'description': 'Updated setting description'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_setting.refresh_from_db()
        self.assertEqual(self.user_setting.value, {'updated': 'value'})
        self.assertEqual(self.user_setting.description, 'Updated setting description')
    
    def test_delete_setting(self):
        """
        Тест удаления настройки.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('core:api:setting-detail', args=[self.user_setting.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверяем, что настройка помечена как удаленная, а не удалена из базы данных
        self.user_setting.refresh_from_db()
        self.assertTrue(self.user_setting.is_deleted)
        self.assertIsNotNone(self.user_setting.deleted_at)
        
        # Проверяем, что общее количество настроек в базе данных не изменилось
        self.assertEqual(Setting.objects.count(), 2)
        
        # Проверяем, что количество неудаленных настроек уменьшилось
        self.assertEqual(Setting.objects.filter(is_deleted=False).count(), 1)

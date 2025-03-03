"""
Тесты безопасности.

Этот модуль содержит тесты для проверки безопасности системы.
"""

import json
from typing import Dict, Any
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Tag, Category, Setting
from core.services.tag_service import TagService
from core.api.permissions import ReadOnlyOrAdmin
from core.data_processing.validators.data_validators import (
    DataValidator,
    StringValidator,
    EmailValidator
)

User = get_user_model()

class SecurityTests(TestCase):
    """
    Тесты безопасности.
    """
    
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        # Создаем пользователей с разными правами
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Создаем клиенты для каждого пользователя
        self.admin_client = Client()
        self.admin_client.login(username='admin', password='adminpass123')
        
        self.staff_client = Client()
        self.staff_client.login(username='staff', password='staffpass123')
        
        self.user_client = Client()
        self.user_client.login(username='user', password='userpass123')
        
        self.anonymous_client = Client()
    
    def test_permission_checks(self):
        """
        Тест проверки прав доступа.
        """
        # Создаем тег для тестирования
        tag = Tag.objects.create(
            name='Test Tag',
            created_by=self.admin_user
        )
        
        # URL для API
        tag_url = reverse('core:api:tag-detail', args=[tag.id])
        
        # Тест доступа для анонимного пользователя
        response = self.anonymous_client.get(tag_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Тест доступа для обычного пользователя (только чтение)
        response = self.user_client.get(tag_url)
        self.assertEqual(response.status_code, 200)  # OK
        
        response = self.user_client.delete(tag_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Тест доступа для администратора (полный доступ)
        response = self.admin_client.get(tag_url)
        self.assertEqual(response.status_code, 200)  # OK
        
        response = self.admin_client.delete(tag_url)
        self.assertEqual(response.status_code, 204)  # No Content
    
    def test_xss_prevention(self):
        """
        Тест предотвращения XSS атак.
        """
        # Пытаемся создать тег с вредоносным JavaScript
        xss_payload = 'Alert XSS'
        
        tag = Tag.objects.create(
            name=xss_payload,
            description='<script>alert("XSS")</script>',
            created_by=self.admin_user
        )
        
        # Получаем тег через API
        response = self.admin_client.get(
            reverse('core:api:tag-detail', args=[tag.id])
        )
        
        data = response.json()
        
        # Проверяем, что JavaScript был экранирован
        self.assertEqual(data['name'], xss_payload)
        self.assertNotEqual(data['description'], '<script>alert("XSS")</script>')
        self.assertIn('&lt;script&gt;', data['description'])
    
    def test_sql_injection_prevention(self):
        """
        Тест предотвращения SQL-инъекций.
        """
        # Пытаемся выполнить SQL-инъекцию через параметры фильтрации
        sql_injection = "' OR '1'='1"
        
        # Создаем тестовый тег
        Tag.objects.create(
            name='Test Tag',
            created_by=self.admin_user
        )
        
        # Пытаемся получить теги через API с вредоносным параметром
        response = self.admin_client.get(
            reverse('core:api:tag-list'),
            {'name': sql_injection}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Проверяем, что SQL-инъекция не сработала
        self.assertEqual(len(data), 0)  # Не должно быть найдено тегов
    
    def test_csrf_protection(self):
        """
        Тест защиты от CSRF атак.
        """
        # Создаем тег для тестирования
        tag = Tag.objects.create(
            name='Test Tag',
            created_by=self.admin_user
        )
        
        # Пытаемся отправить POST запрос без CSRF токена
        client = Client(enforce_csrf_checks=True)
        client.login(username='admin', password='adminpass123')
        
        response = client.post(
            reverse('core:api:tag-list'),
            {'name': 'New Tag'}
        )
        
        # Запрос должен быть отклонен
        self.assertEqual(response.status_code, 403)
    
    def test_input_validation(self):
        """
        Тест валидации входных данных.
        """
        # Тестируем валидатор строк
        validator = StringValidator(
            field_name='name',
            min_length=3,
            max_length=50,
            not_contains=['<script>', 'javascript:']
        )
        
        # Проверяем корректные данные
        result = validator.validate('Test Name')
        self.assertTrue(result.is_valid())
        
        # Проверяем слишком короткую строку
        result = validator.validate('Te')
        self.assertFalse(result.is_valid())
        
        # Проверяем слишком длинную строку
        result = validator.validate('T' * 51)
        self.assertFalse(result.is_valid())
        
        # Проверяем строку с запрещенным содержимым
        result = validator.validate('Test <script>alert("XSS")</script>')
        self.assertFalse(result.is_valid())
        
        # Тестируем валидатор email
        email_validator = EmailValidator(
            field_name='email',
            required=True
        )
        
        # Проверяем корректный email
        result = email_validator.validate('test@example.com')
        self.assertTrue(result.is_valid())
        
        # Проверяем некорректный email
        result = email_validator.validate('invalid-email')
        self.assertFalse(result.is_valid())
    
    def test_file_upload_security(self):
        """
        Тест безопасности загрузки файлов.
        """
        # Пытаемся загрузить файл с вредоносным расширением
        malicious_file = SimpleUploadedFile(
            'malicious.php',
            b'<?php echo "Malicious code"; ?>',
            content_type='application/x-php'
        )
        
        response = self.admin_client.post(
            reverse('core:api:file-list'),
            {'file': malicious_file}
        )
        
        # Загрузка должна быть отклонена
        self.assertEqual(response.status_code, 400)
        
        # Пытаемся загрузить слишком большой файл
        large_file = SimpleUploadedFile(
            'large.txt',
            b'0' * (10 * 1024 * 1024),  # 10MB
            content_type='text/plain'
        )
        
        response = self.admin_client.post(
            reverse('core:api:file-list'),
            {'file': large_file}
        )
        
        # Загрузка должна быть отклонена
        self.assertEqual(response.status_code, 400)
    
    def test_rate_limiting(self):
        """
        Тест ограничения частоты запросов.
        """
        # Делаем множество запросов за короткий промежуток времени
        for _ in range(100):
            response = self.anonymous_client.get(
                reverse('core:api:tag-list')
            )
        
        # Последний запрос должен быть отклонен
        self.assertEqual(response.status_code, 429)  # Too Many Requests
    
    def test_sensitive_data_exposure(self):
        """
        Тест защиты конфиденциальных данных.
        """
        # Создаем настройку с конфиденциальными данными
        setting = Setting.objects.create(
            key='api.secret_key',
            value='super_secret_value',
            created_by=self.admin_user
        )
        
        # Пытаемся получить настройку через API
        response = self.user_client.get(
            reverse('core:api:setting-detail', args=[setting.id])
        )
        
        # Проверяем, что значение скрыто
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotEqual(data['value'], 'super_secret_value')
        self.assertEqual(data['value'], '********')
    
    def test_authentication_security(self):
        """
        Тест безопасности аутентификации.
        """
        # Пытаемся войти с некорректными данными
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'admin', 'password': 'wrong_password'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        # Пытаемся получить доступ к защищенному ресурсу без аутентификации
        response = self.anonymous_client.get(
            reverse('core:api:tag-list')
        )
        
        self.assertEqual(response.status_code, 403)
        
        # Проверяем блокировку после нескольких неудачных попыток
        for _ in range(5):
            response = self.client.post(
                reverse('token_obtain_pair'),
                {'username': 'admin', 'password': 'wrong_password'}
            )
        
        # Следующая попытка должна быть заблокирована
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'admin', 'password': 'adminpass123'}
        )
        
        self.assertEqual(response.status_code, 403) 
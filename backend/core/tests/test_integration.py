"""
Интеграционные тесты.

Этот модуль содержит интеграционные тесты для проверки взаимодействия
между различными компонентами системы.
"""

import os
from typing import List, Dict, Any
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from core.models import Tag, Category, TaggedItem
from core.services.tag_service import TagService
from core.templates_engine.renderers import HTMLTemplateRenderer, PDFTemplateRenderer
from core.data_processing.processors.chunk_processor import ChunkProcessor
from core.cache.cache_manager import CacheManager
from core.signals.handlers import handle_tag_created, handle_tag_updated, handle_tag_deleted

User = get_user_model()

class TagIntegrationTests(TestCase):
    """
    Интеграционные тесты для тегов.
    """
    
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tag_service = TagService(user=self.user)
        
        # Очищаем кеш перед каждым тестом
        cache.clear()
    
    def test_tag_lifecycle(self):
        """
        Тест полного жизненного цикла тега.
        """
        # Создание тега
        tag = self.tag_service.create_tag(
            name='Test Tag',
            color='#FF0000',
            description='Test description'
        )
        
        self.assertIsNotNone(tag)
        self.assertEqual(tag.name, 'Test Tag')
        
        # Проверяем, что тег появился в кеше
        cached_tag = cache.get(f'tag:{tag.id}')
        self.assertIsNotNone(cached_tag)
        
        # Обновление тега
        updated_tag = self.tag_service.update_tag(
            tag=tag,
            name='Updated Tag',
            color='#00FF00'
        )
        
        self.assertEqual(updated_tag.name, 'Updated Tag')
        self.assertEqual(updated_tag.color, '#00FF00')
        
        # Проверяем обновление в кеше
        cached_updated_tag = cache.get(f'tag:{tag.id}')
        self.assertEqual(cached_updated_tag.name, 'Updated Tag')
        
        # Удаление тега
        self.tag_service.delete_tag(tag)
        
        # Проверяем удаление из базы
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
        
        # Проверяем удаление из кеша
        cached_deleted_tag = cache.get(f'tag:{tag.id}')
        self.assertIsNone(cached_deleted_tag)
    
    def test_tag_with_category(self):
        """
        Тест создания тега с категорией и проверка связей.
        """
        # Создаем категорию
        category = self.tag_service.create_category(
            name='Test Category',
            description='Test category description'
        )
        
        # Создаем тег в категории
        tag = self.tag_service.create_tag(
            name='Test Tag',
            category=category
        )
        
        # Проверяем связь
        self.assertEqual(tag.category, category)
        
        # Получаем теги категории
        category_tags = self.tag_service.get_tags_by_category(category)
        self.assertEqual(len(category_tags), 1)
        self.assertEqual(category_tags[0], tag)
    
    def test_tag_object_relations(self):
        """
        Тест связей тега с объектами.
        """
        # Создаем тег
        tag = self.tag_service.create_tag(name='Test Tag')
        
        # Создаем тестовый объект (пользователя)
        test_obj = User.objects.create_user(
            username='taggeduser',
            email='tagged@example.com',
            password='testpass123'
        )
        
        # Добавляем тег к объекту
        tagged_items = self.tag_service.tag_object(test_obj, [tag])
        self.assertEqual(len(tagged_items), 1)
        
        # Получаем объекты с тегом
        tagged_objects = self.tag_service.get_objects_with_tag(tag, User)
        self.assertEqual(len(tagged_objects), 1)
        self.assertEqual(tagged_objects[0], test_obj)
        
        # Получаем теги объекта
        object_tags = self.tag_service.get_tags_for_object(test_obj)
        self.assertEqual(len(object_tags), 1)
        self.assertEqual(object_tags[0], tag)
        
        # Удаляем тег с объекта
        self.tag_service.remove_tag_from_object(test_obj, tag)
        
        # Проверяем удаление связи
        self.assertEqual(len(self.tag_service.get_tags_for_object(test_obj)), 0)

class TemplateIntegrationTests(TestCase):
    """
    Интеграционные тесты для шаблонов.
    """
    
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.html_renderer = HTMLTemplateRenderer()
        self.pdf_renderer = PDFTemplateRenderer()
        
        # Создаем временную директорию для тестовых файлов
        self.test_output_dir = os.path.join(settings.MEDIA_ROOT, 'test_output')
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """
        Очистка после тестов.
        """
        # Удаляем тестовые файлы
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
    
    def test_html_template_rendering(self):
        """
        Тест рендеринга HTML шаблона.
        """
        template_content = """
        <html>
        <body>
            <h1>{{ title }}</h1>
            <p>{{ content }}</p>
            {% for item in items %}
            <li>{{ item }}</li>
            {% endfor %}
        </body>
        </html>
        """
        
        context = {
            'title': 'Test Title',
            'content': 'Test Content',
            'items': ['Item 1', 'Item 2', 'Item 3']
        }
        
        # Рендерим шаблон
        rendered_html = self.html_renderer.render(template_content, context)
        
        # Проверяем результат
        self.assertIn('Test Title', rendered_html)
        self.assertIn('Test Content', rendered_html)
        self.assertIn('Item 1', rendered_html)
        
        # Сохраняем в файл
        output_path = os.path.join(self.test_output_dir, 'test.html')
        self.html_renderer.render_to_file(template_content, context, output_path)
        
        # Проверяем создание файла
        self.assertTrue(os.path.exists(output_path))
    
    def test_pdf_template_rendering(self):
        """
        Тест рендеринга PDF шаблона.
        """
        template_content = """
        <html>
        <body>
            <h1>{{ title }}</h1>
            <p>{{ content }}</p>
        </body>
        </html>
        """
        
        context = {
            'title': 'PDF Test',
            'content': 'PDF Content'
        }
        
        # Сохраняем в PDF
        output_path = os.path.join(self.test_output_dir, 'test.pdf')
        self.pdf_renderer.render_to_file(template_content, context, output_path)
        
        # Проверяем создание файла
        self.assertTrue(os.path.exists(output_path))
        
        # Проверяем, что это действительно PDF
        with open(output_path, 'rb') as f:
            self.assertTrue(f.read().startswith(b'%PDF'))

class DataProcessingIntegrationTests(TestCase):
    """
    Интеграционные тесты для обработки данных.
    """
    
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.processor = ChunkProcessor(chunk_size=10)
        self.cache_manager = CacheManager()
    
    def test_batch_tag_processing(self):
        """
        Тест пакетной обработки тегов.
        """
        # Создаем тестовые данные
        test_data = [
            {'name': f'Tag {i}', 'color': '#FF0000'} 
            for i in range(100)
        ]
        
        # Функция обработки
        def process_tag(data):
            tag = Tag.objects.create(**data)
            return tag
        
        # Обрабатываем данные
        result = self.processor.process_data(test_data, process_tag)
        
        # Проверяем результаты
        self.assertTrue(result.success)
        self.assertEqual(result.processed_count, 100)
        self.assertEqual(result.success_count, 100)
        self.assertEqual(len(result.errors), 0)
        
        # Проверяем создание тегов в базе
        self.assertEqual(Tag.objects.count(), 100)
    
    def test_cached_tag_processing(self):
        """
        Тест обработки тегов с использованием кеша.
        """
        # Создаем тег
        tag = Tag.objects.create(name='Cache Test Tag')
        
        # Сохраняем в кеш
        self.cache_manager.set_tag(tag)
        
        # Получаем из кеша
        cached_tag = self.cache_manager.get_tag(tag.id)
        self.assertEqual(cached_tag.name, 'Cache Test Tag')
        
        # Обновляем тег
        tag.name = 'Updated Cache Tag'
        tag.save()
        
        # Проверяем обновление в кеше
        updated_cached_tag = self.cache_manager.get_tag(tag.id)
        self.assertEqual(updated_cached_tag.name, 'Updated Cache Tag')
        
        # Удаляем тег
        tag.hard_delete()
        
        # Проверяем удаление из кеша
        deleted_cached_tag = self.cache_manager.get_tag(tag.id)
        self.assertIsNone(deleted_cached_tag) 
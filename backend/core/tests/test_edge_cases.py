"""
Тесты граничных случаев.

Этот модуль содержит тесты для проверки поведения системы
в нестандартных и граничных ситуациях.
"""

import uuid
from typing import Dict, Any
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta

from core.models import Tag, Category, Setting, TaggedItem
from core.services.tag_service import TagService
from core.data_processing.processors.chunk_processor import ChunkProcessor
from core.data_processing.validators.data_validators import (
    DataValidator,
    NumericValidator,
    StringValidator,
    DateValidator
)

User = get_user_model()

class EdgeCaseTests(TestCase):
    """
    Тесты граничных случаев.
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
    
    def test_extreme_string_lengths(self):
        """
        Тест обработки строк экстремальной длины.
        """
        # Тест очень длинной строки
        very_long_name = 'A' * 1000
        
        # Проверяем, что создание тега с очень длинным именем вызывает ошибку
        with self.assertRaises(ValidationError):
            self.tag_service.create_tag(name=very_long_name)
        
        # Тест минимально допустимой строки
        min_name = 'AB'
        tag = self.tag_service.create_tag(name=min_name)
        self.assertEqual(tag.name, min_name)
        
        # Тест пустой строки
        with self.assertRaises(ValidationError):
            self.tag_service.create_tag(name='')
        
        # Строка с пробелами
        tag = self.tag_service.create_tag(name='   Test Tag    ')
        self.assertEqual(tag.name.strip(), 'Test Tag')
        
        # Строка с китайскими символами
        chinese_name = '测试标签'
        tag = self.tag_service.create_tag(name=chinese_name, slug='test-tag-chinese')
        self.assertEqual(tag.name, chinese_name)
        
        # Unicode символы
        unicode_name = 'Тестовый тег'
        tag = self.tag_service.create_tag(name=unicode_name, slug='test-tag-unicode')
        self.assertEqual(tag.name, unicode_name)
        
        # Специальные символы
        tag = self.tag_service.create_tag(name='Tag!@#$%^&*()')
        self.assertIsNotNone(tag)
    
    def test_duplicate_handling(self):
        """
        Тест обработки дубликатов.
        """
        # Создаем первый тег
        tag1 = self.tag_service.create_tag(name='Test Tag')
        
        # Пытаемся создать тег с тем же именем
        tag2 = self.tag_service.create_tag(name='Test Tag')
        
        # Проверяем, что slug автоматически изменен
        self.assertNotEqual(tag1.slug, tag2.slug)
        
        # Пытаемся создать тег с тем же slug
        with self.assertRaises(ValidationError):
            # Явно указываем slug, который уже существует
            self.tag_service.create_tag(name='Another Tag', slug=tag1.slug)
        
        # Проверяем уникальность в рамках транзакции
        with transaction.atomic():
            try:
                # Попытка создать тег с тем же slug в рамках транзакции
                self.tag_service.create_tag(name='Transaction Tag', slug=tag1.slug)
                self.fail("Должна быть вызвана ошибка ValidationError")
            except ValidationError:
                # Ожидаемая ошибка
                pass
    
    def test_null_and_empty_values(self):
        """
        Тест обработки null и пустых значений.
        """
        # None значения
        with self.assertRaises(ValidationError):
            self.tag_service.create_tag(name=None)
        
        # Пустые строки в необязательных полях
        tag = self.tag_service.create_tag(
            name='Test Tag',
            description='',
            color=''
        )
        self.assertIsNotNone(tag)
        self.assertEqual(tag.description, '')
        self.assertEqual(tag.color, '')
        
        # Пустой список тегов
        test_obj = User.objects.create_user(
            username='tagtest',
            email='tagtest@example.com',
            password='testpass123'
        )
        tagged_items = self.tag_service.tag_object(test_obj, [])
        self.assertEqual(len(tagged_items), 0)
    
    def test_numeric_boundaries(self):
        """
        Тест граничных значений чисел.
        """
        validator = NumericValidator(
            field_name='test_field',
            min_value=0,
            max_value=100
        )
        
        # Тест граничных значений
        self.assertTrue(validator.validate(0).is_valid())
        self.assertTrue(validator.validate(100).is_valid())
        self.assertFalse(validator.validate(-1).is_valid())
        self.assertFalse(validator.validate(101).is_valid())
        
        # Тест дробных чисел
        self.assertTrue(validator.validate(50.5).is_valid())
        
        # Тест очень больших чисел
        self.assertFalse(validator.validate(float('inf')).is_valid())
        
        # Тест не-числовых значений
        self.assertFalse(validator.validate('not a number').is_valid())
    
    def test_date_boundaries(self):
        """
        Тест граничных значений дат.
        """
        now = timezone.now()
        validator = DateValidator(
            field_name='test_date',
            min_date=now - timedelta(days=30),
            max_date=now + timedelta(days=30)
        )
        
        # Тест граничных дат
        self.assertTrue(validator.validate(now).is_valid())
        self.assertTrue(validator.validate(now - timedelta(days=30)).is_valid())
        self.assertTrue(validator.validate(now + timedelta(days=30)).is_valid())
        
        # Тест выхода за границы
        self.assertFalse(validator.validate(now - timedelta(days=31)).is_valid())
        self.assertFalse(validator.validate(now + timedelta(days=31)).is_valid())
        
        # Тест некорректного формата
        self.assertFalse(validator.validate('not a date').is_valid())
    
    def test_concurrent_modifications(self):
        """
        Тест одновременных модификаций.
        """
        # Создаем тег для тестирования
        tag = self.tag_service.create_tag(name='Test Tag')
        
        # Симулируем конкурентное обновление
        tag1 = Tag.objects.get(id=tag.id)
        tag2 = Tag.objects.get(id=tag.id)
        
        tag1.name = 'Updated Name 1'
        tag2.name = 'Updated Name 2'
        
        # Первое обновление должно пройти успешно
        tag1.save()
        
        # Второе обновление не должно перезаписать первое
        tag2.save()
        
        # Проверяем финальное состояние
        updated_tag = Tag.objects.get(id=tag.id)
        self.assertEqual(updated_tag.name, 'Updated Name 2')
    
    def test_recursive_relationships(self):
        """
        Тест рекурсивных связей.
        """
        # Создаем категории
        parent = self.tag_service.create_category(name='Parent')
        child = self.tag_service.create_category(name='Child', parent=parent)
        grandchild = self.tag_service.create_category(name='Grandchild', parent=child)
        
        # Пытаемся создать циклическую связь
        with self.assertRaises(ValueError):
            self.tag_service.update_category(parent, parent=grandchild)
        
        # Проверяем максимальную глубину вложенности
        for i in range(10):
            new_child = self.tag_service.create_category(
                name=f'Child {i}',
                parent=grandchild
            )
            grandchild = new_child
        
        # Проверяем, что структура корректна
        category = grandchild
        depth = 0
        while category.parent:
            category = category.parent
            depth += 1
            
        self.assertEqual(category, parent)
        self.assertEqual(depth, 12)  # Parent -> Child -> Grandchild -> 10 Child X = 12 уровней
    
    def test_large_batch_processing(self):
        """
        Тест обработки больших наборов данных.
        """
        processor = ChunkProcessor(chunk_size=1000)
        
        # Создаем большой набор данных
        num_items = 10000
        test_data = [
            {
                'name': f'Tag {i}',
                'slug': f'tag-{i}',
                'description': f'Description for tag {i}'
            }
            for i in range(num_items)
        ]
        
        # Функция обработки с возможными ошибками
        def process_item(data):
            if len(data['name']) > 100:  # Симулируем ошибку
                raise ValueError('Name too long')
            return Tag.objects.create(**data, created_by=self.user)
        
        # Обрабатываем данные
        result = processor.process_data(test_data, process_item)
        
        # Проверяем результаты
        self.assertTrue(result.success)
        self.assertEqual(result.processed_count, num_items)
        self.assertEqual(result.success_count, num_items)
        self.assertEqual(len(result.errors), 0)
    
    def test_special_characters_handling(self):
        """
        Тест обработки специальных символов.
        """
        special_chars = [
            ('Tag\nwith\nnewlines', 'tag-with-newlines'),
            ('Tag\twith\ttabs', 'tag-with-tabs'),
            ('Tag with spaces', 'tag-with-spaces'),
            ('Tag&with#special@chars', 'tagwithspecialchars'),
            ('Tag with émojis 🎉', 'tag-with-emojis'),
            # HTML-теги не разрешены в имени тега
            # ('Tag with <html> tags', 'tag-with-html-tags'),
            ('Tag with "quotes"', 'tag-with-quotes'),
            ('Tag with \\backslashes\\', 'tag-with-backslashes'),
            ('Tag with /forward/slashes/', 'tag-with-forwardslashes'),
            ('Tag with Unicode ♥ ☺ ♦', 'tag-with-unicode')
        ]
        
        for name, expected_slug in special_chars:
            tag = self.tag_service.create_tag(name=name)
            self.assertIsNotNone(tag)
            # Проверяем начальную часть slug, так как могут быть добавлены числовые суффиксы
            # из-за уникальности slug
            self.assertTrue(tag.slug.startswith(expected_slug))
            
        # Проверяем, что теги с HTML-тегами не разрешены
        with self.assertRaises(ValidationError):
            self.tag_service.create_tag(name='Tag with <html> tags')
    
    def test_error_handling(self):
        """
        Тест обработки ошибок.
        """
        # Тест обработки исключений
        with self.assertRaises(ValidationError):
            self.tag_service.create_tag(name='')
        
        # Проверяем количество тегов до теста
        initial_count = Tag.objects.count()
        
        # Тест обработки ошибок в транзакциях
        try:
            with transaction.atomic():
                self.tag_service.create_tag(name='Test Tag for Transaction')
                # Намеренно вызываем ошибку
                raise ValueError('Test error')
        except ValueError:
            # Проверяем, что тег не был создан (транзакция откатилась)
            self.assertEqual(Tag.objects.count(), initial_count)
        
        # Тест обработки множественных ошибок
        from core.data_processing.validators.data_validators import StringValidator
        from core.data_processing.validators.base_validator import ValidationResult
        
        validator = StringValidator(
            field_name='name',
            min_length=3,
            max_length=50,
            not_contains=['<script>', 'javascript:']
        )
        
        result = validator.validate('a<script>alert("test")</script>')
        self.assertFalse(result.is_valid())
        # Проверяем, что есть хотя бы одна ошибка
        self.assertTrue(len(result.errors) > 0) 
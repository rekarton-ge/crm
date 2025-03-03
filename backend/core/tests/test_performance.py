"""
Тесты производительности.

Этот модуль содержит тесты для проверки производительности
различных компонентов системы.
"""

import time
import random
from typing import List, Dict, Any
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test.utils import override_settings
from django.db import connection
from django.db.models import Q

from core.models import Tag, Category, TaggedItem
from core.services.tag_service import TagService
from core.data_processing.processors.chunk_processor import BulkChunkProcessor
from core.cache.cache_manager import CacheManager

User = get_user_model()

class TagPerformanceTests(TransactionTestCase):
    """
    Тесты производительности для работы с тегами.
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
        self.processor = BulkChunkProcessor(chunk_size=1000)
        
        # Очищаем кеш
        cache.clear()
    
    def test_bulk_tag_creation_performance(self):
        """
        Тест производительности массового создания тегов.
        """
        num_tags = 10000
        
        # Подготавливаем данные
        tag_data = [
            {
                'name': f'Tag {i}',
                'slug': f'tag-{i}',
                'color': f'#{random.randint(0, 0xFFFFFF):06x}',
                'description': f'Description for tag {i}'
            }
            for i in range(num_tags)
        ]
        
        # Замеряем время выполнения
        start_time = time.time()
        
        # Создаем теги с использованием bulk_create
        result = self.processor.bulk_create(Tag, tag_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверяем результаты
        self.assertTrue(result.success)
        self.assertEqual(result.processed_count, num_tags)
        self.assertEqual(result.success_count, num_tags)
        self.assertEqual(Tag.objects.count(), num_tags)
        
        # Проверяем производительность
        self.assertLess(execution_time, 10.0)  # Должно выполниться менее чем за 10 секунд
        
        # Выводим метрики
        tags_per_second = num_tags / execution_time
        print(f"\nПроизводительность создания тегов:")
        print(f"Создано тегов: {num_tags}")
        print(f"Время выполнения: {execution_time:.2f} сек")
        print(f"Тегов в секунду: {tags_per_second:.2f}")
    
    def test_tag_search_performance(self):
        """
        Тест производительности поиска тегов.
        """
        num_tags = 10000
        
        # Создаем теги
        tags = [
            Tag.objects.create(
                name=f'Tag {i}',
                slug=f'tag-{i}',
                color=f'#{random.randint(0, 0xFFFFFF):06x}'
            )
            for i in range(num_tags)
        ]
        
        # Тестируем различные типы поиска
        search_tests = [
            ('Точный поиск по ID', lambda: Tag.objects.get(id=tags[0].id)),
            ('Поиск по имени', lambda: Tag.objects.filter(name='Tag 1').first()),
            ('Поиск по частичному совпадению', lambda: Tag.objects.filter(name__contains='Tag').count()),
            ('Сложный поиск', lambda: Tag.objects.filter(
                Q(name__contains='Tag') & Q(color__startswith='#')
            ).count())
        ]
        
        print("\nПроизводительность поиска тегов:")
        
        for test_name, search_func in search_tests:
            # Очищаем кеш перед каждым тестом
            cache.clear()
            
            # Замеряем время выполнения
            start_time = time.time()
            
            # Выполняем поиск 100 раз
            for _ in range(100):
                search_func()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n{test_name}:")
            print(f"Время выполнения (100 запросов): {execution_time:.2f} сек")
            print(f"Среднее время запроса: {(execution_time / 100):.4f} сек")
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_cache_performance(self):
        """
        Тест производительности кеширования.
        """
        num_tags = 1000
        cache_manager = CacheManager()
        
        # Создаем теги
        tags = [
            Tag.objects.create(
                name=f'Tag {i}',
                slug=f'tag-{i}',
                color=f'#{random.randint(0, 0xFFFFFF):06x}'
            )
            for i in range(num_tags)
        ]
        
        print("\nПроизводительность кеширования:")
        
        # Тест записи в кеш
        start_time = time.time()
        for tag in tags:
            cache_manager.set_tag(tag)
        write_time = time.time() - start_time
        
        print(f"Время записи {num_tags} тегов в кеш: {write_time:.2f} сек")
        print(f"Среднее время записи: {(write_time / num_tags):.4f} сек")
        
        # Тест чтения из кеша
        start_time = time.time()
        for tag in tags:
            cached_tag = cache_manager.get_tag(tag.id)
            self.assertIsNotNone(cached_tag)
        read_time = time.time() - start_time
        
        print(f"Время чтения {num_tags} тегов из кеша: {read_time:.2f} сек")
        print(f"Среднее время чтения: {(read_time / num_tags):.4f} сек")

class DataProcessingPerformanceTests(TransactionTestCase):
    """
    Тесты производительности обработки данных.
    """
    
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.processor = BulkChunkProcessor(
            chunk_size=1000,
            parallel_processing=True,
            max_workers=4
        )
    
    def test_parallel_processing_performance(self):
        """
        Тест производительности параллельной обработки данных.
        """
        num_items = 10000
        
        # Создаем тестовые данные
        test_data = [
            {'index': i, 'value': random.random()}
            for i in range(num_items)
        ]
        
        def process_item(data):
            # Имитируем сложную обработку
            time.sleep(0.001)
            return data['index'] * data['value']
        
        print("\nПроизводительность параллельной обработки:")
        
        # Тест последовательной обработки
        sequential_processor = BulkChunkProcessor(
            chunk_size=1000,
            parallel_processing=False
        )
        
        start_time = time.time()
        sequential_result = sequential_processor.process_data(test_data, process_item)
        sequential_time = time.time() - start_time
        
        print(f"Последовательная обработка {num_items} элементов: {sequential_time:.2f} сек")
        
        # Тест параллельной обработки
        start_time = time.time()
        parallel_result = self.processor.process_data(test_data, process_item)
        parallel_time = time.time() - start_time
        
        print(f"Параллельная обработка {num_items} элементов: {parallel_time:.2f} сек")
        print(f"Ускорение: {sequential_time / parallel_time:.2f}x")
        
        # Проверяем результаты
        self.assertTrue(sequential_result.success)
        self.assertTrue(parallel_result.success)
        self.assertEqual(sequential_result.processed_count, num_items)
        self.assertEqual(parallel_result.processed_count, num_items)
    
    def test_database_batch_operations_performance(self):
        """
        Тест производительности пакетных операций с базой данных.
        """
        num_items = 10000
        
        print("\nПроизводительность пакетных операций с БД:")
        
        # Тест bulk_create
        tag_data = [
            {
                'name': f'Tag {i}',
                'slug': f'tag-{i}',
                'color': f'#{random.randint(0, 0xFFFFFF):06x}'
            }
            for i in range(num_items)
        ]
        
        start_time = time.time()
        result = self.processor.bulk_create(Tag, tag_data)
        create_time = time.time() - start_time
        
        print(f"Bulk create {num_items} тегов: {create_time:.2f} сек")
        
        # Тест bulk_update
        update_data = Tag.objects.all()
        for tag in update_data:
            tag.color = f'#{random.randint(0, 0xFFFFFF):06x}'
        
        start_time = time.time()
        result = self.processor.bulk_update(
            queryset=Tag.objects.all(),
            update_func=lambda x: x,
            update_fields=['color']
        )
        update_time = time.time() - start_time
        
        print(f"Bulk update {num_items} тегов: {update_time:.2f} сек")
        
        # Проверяем количество запросов к БД
        with connection.execute_wrapper(self._count_queries):
            self.query_count = 0
            Tag.objects.all().delete()
            
        print(f"Количество запросов для удаления {num_items} тегов: {self.query_count}")
    
    def _count_queries(self, execute, sql, params, many, context):
        """
        Подсчет количества SQL запросов.
        """
        self.query_count += 1
        return execute(sql, params, many, context) 
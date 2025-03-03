"""
Модуль для оптимизации SQL-запросов.

Этот модуль предоставляет инструменты для анализа и оптимизации SQL-запросов в Django.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from django.db import connection
from django.db.models import QuerySet, Model
from django.db.models.query import QuerySet
from django.conf import settings

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Класс для оптимизации SQL-запросов.
    """
    
    def __init__(self, log_level: str = 'DEBUG'):
        """
        Инициализирует оптимизатор запросов.
        
        Args:
            log_level: Уровень логирования
        """
        self.log_level = getattr(logging, log_level)
    
    def analyze_query(self, queryset: QuerySet) -> Dict[str, Any]:
        """
        Анализирует запрос и возвращает информацию о нем.
        
        Args:
            queryset: Запрос для анализа
            
        Returns:
            Dict[str, Any]: Информация о запросе
        """
        # Получаем SQL-запрос
        sql, params = queryset.query.sql_with_params()
        
        # Анализируем план выполнения запроса
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN ANALYZE {sql}", params)
            plan = cursor.fetchall()
        
        # Парсим план выполнения
        plan_info = self._parse_explain_output(plan)
        
        # Логируем результаты
        logger.log(self.log_level, f"Query analysis:\n{plan_info['raw_plan']}")
        
        return plan_info
    
    def _parse_explain_output(self, plan: List[Tuple]) -> Dict[str, Any]:
        """
        Парсит вывод команды EXPLAIN ANALYZE.
        
        Args:
            plan: Вывод команды EXPLAIN ANALYZE
            
        Returns:
            Dict[str, Any]: Информация о плане выполнения
        """
        raw_plan = "\n".join(row[0] for row in plan)
        
        # Извлекаем информацию о времени выполнения
        execution_time_match = re.search(r"Execution time: ([\d.]+) ms", raw_plan)
        execution_time = float(execution_time_match.group(1)) if execution_time_match else None
        
        # Извлекаем информацию о сканировании таблиц
        table_scans = re.findall(r"Seq Scan on (\w+)", raw_plan)
        
        # Извлекаем информацию об индексах
        index_scans = re.findall(r"Index Scan using (\w+) on (\w+)", raw_plan)
        
        # Извлекаем информацию о соединениях
        joins = re.findall(r"(Hash|Merge|Nested Loop) Join", raw_plan)
        
        return {
            'raw_plan': raw_plan,
            'execution_time': execution_time,
            'table_scans': table_scans,
            'index_scans': index_scans,
            'joins': joins
        }
    
    def optimize_queryset(self, queryset: QuerySet, 
                          select_related: Optional[List[str]] = None,
                          prefetch_related: Optional[List[str]] = None,
                          only: Optional[List[str]] = None,
                          defer: Optional[List[str]] = None) -> QuerySet:
        """
        Оптимизирует запрос.
        
        Args:
            queryset: Запрос для оптимизации
            select_related: Список полей для select_related
            prefetch_related: Список полей для prefetch_related
            only: Список полей для only
            defer: Список полей для defer
            
        Returns:
            QuerySet: Оптимизированный запрос
        """
        # Применяем select_related
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        # Применяем prefetch_related
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        # Применяем only
        if only:
            queryset = queryset.only(*only)
        
        # Применяем defer
        if defer:
            queryset = queryset.defer(*defer)
        
        return queryset
    
    def detect_n_plus_1(self, queryset: QuerySet) -> Dict[str, Any]:
        """
        Обнаруживает проблему N+1 запросов.
        
        Args:
            queryset: Запрос для анализа
            
        Returns:
            Dict[str, Any]: Информация о проблеме N+1
        """
        # Сохраняем количество запросов до выполнения
        queries_before = len(connection.queries)
        
        # Выполняем запрос и итерируемся по результатам
        results = list(queryset)
        for result in results:
            # Доступ к атрибутам объекта для проверки наличия дополнительных запросов
            str(result)
        
        # Сохраняем количество запросов после выполнения
        queries_after = len(connection.queries)
        
        # Вычисляем количество дополнительных запросов
        additional_queries = queries_after - queries_before
        
        # Определяем, есть ли проблема N+1
        has_n_plus_1 = additional_queries > len(results)
        
        return {
            'has_n_plus_1': has_n_plus_1,
            'total_queries': additional_queries,
            'results_count': len(results),
            'additional_queries_per_result': additional_queries / len(results) if results else 0
        }
    
    def suggest_indexes(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Предлагает индексы для оптимизации запроса.
        
        Args:
            queryset: Запрос для анализа
            
        Returns:
            List[Dict[str, Any]]: Список предлагаемых индексов
        """
        # Получаем SQL-запрос
        sql, params = queryset.query.sql_with_params()
        
        # Анализируем запрос
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {sql}", params)
            plan = cursor.fetchall()
        
        # Парсим план выполнения
        plan_info = self._parse_explain_output(plan)
        
        # Ищем последовательные сканирования таблиц
        table_scans = plan_info['table_scans']
        
        # Ищем условия WHERE в запросе
        where_conditions = re.findall(r"WHERE\s+(.+?)(?:\s+GROUP BY|\s+ORDER BY|\s+LIMIT|\s*$)", sql, re.IGNORECASE)
        
        # Извлекаем поля из условий WHERE
        where_fields = []
        if where_conditions:
            where_fields = re.findall(r'(\w+\.\w+|\w+)\s*[=><]', where_conditions[0])
        
        # Ищем условия ORDER BY в запросе
        order_by_conditions = re.findall(r"ORDER BY\s+(.+?)(?:\s+LIMIT|\s*$)", sql, re.IGNORECASE)
        
        # Извлекаем поля из условий ORDER BY
        order_by_fields = []
        if order_by_conditions:
            order_by_fields = re.findall(r'(\w+\.\w+|\w+)', order_by_conditions[0])
        
        # Формируем предложения по индексам
        suggestions = []
        
        for table in table_scans:
            # Предлагаем индексы для полей в WHERE
            for field in where_fields:
                if '.' in field:
                    table_name, field_name = field.split('.')
                    if table_name == table:
                        suggestions.append({
                            'table': table,
                            'field': field_name,
                            'reason': f"Field {field} used in WHERE condition"
                        })
                else:
                    suggestions.append({
                        'table': table,
                        'field': field,
                        'reason': f"Field {field} used in WHERE condition"
                    })
            
            # Предлагаем индексы для полей в ORDER BY
            for field in order_by_fields:
                if '.' in field:
                    table_name, field_name = field.split('.')
                    if table_name == table:
                        suggestions.append({
                            'table': table,
                            'field': field_name,
                            'reason': f"Field {field} used in ORDER BY clause"
                        })
                else:
                    suggestions.append({
                        'table': table,
                        'field': field,
                        'reason': f"Field {field} used in ORDER BY clause"
                    })
        
        return suggestions


def optimize_queryset(queryset: QuerySet, 
                     select_related: Optional[List[str]] = None,
                     prefetch_related: Optional[List[str]] = None,
                     only: Optional[List[str]] = None,
                     defer: Optional[List[str]] = None) -> QuerySet:
    """
    Оптимизирует запрос.
    
    Args:
        queryset: Запрос для оптимизации
        select_related: Список полей для select_related
        prefetch_related: Список полей для prefetch_related
        only: Список полей для only
        defer: Список полей для defer
        
    Returns:
        QuerySet: Оптимизированный запрос
    """
    optimizer = QueryOptimizer()
    return optimizer.optimize_queryset(
        queryset, select_related, prefetch_related, only, defer
    )


def analyze_query_plan(queryset: QuerySet) -> Dict[str, Any]:
    """
    Анализирует план выполнения запроса.
    
    Args:
        queryset: Запрос для анализа
        
    Returns:
        Dict[str, Any]: Информация о плане выполнения
    """
    optimizer = QueryOptimizer()
    return optimizer.analyze_query(queryset)


def detect_n_plus_1(queryset: QuerySet) -> Dict[str, Any]:
    """
    Обнаруживает проблему N+1 запросов.
    
    Args:
        queryset: Запрос для анализа
        
    Returns:
        Dict[str, Any]: Информация о проблеме N+1
    """
    optimizer = QueryOptimizer()
    return optimizer.detect_n_plus_1(queryset)


def suggest_indexes(queryset: QuerySet) -> List[Dict[str, Any]]:
    """
    Предлагает индексы для оптимизации запроса.
    
    Args:
        queryset: Запрос для анализа
        
    Returns:
        List[Dict[str, Any]]: Список предлагаемых индексов
    """
    optimizer = QueryOptimizer()
    return optimizer.suggest_indexes(queryset)

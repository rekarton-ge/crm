"""
Модуль для обнаружения узких мест в производительности приложения.

Этот модуль предоставляет классы для обнаружения и анализа узких мест в производительности приложения.
"""

import logging
import time
import tracemalloc
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Callable

from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class BottleneckDetector(ABC):
    """
    Базовый класс для детекторов узких мест.
    """
    
    def __init__(self, threshold: Optional[float] = None, log_level: str = 'WARNING'):
        """
        Инициализирует детектор узких мест.
        
        Args:
            threshold: Пороговое значение для определения узкого места
            log_level: Уровень логирования
        """
        self.threshold = threshold
        self.log_level = getattr(logging, log_level)
        self.results = []
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """
        Начинает мониторинг.
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """
        Останавливает мониторинг.
        """
        pass
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Анализирует собранные данные.
        
        Returns:
            Dict[str, Any]: Результаты анализа
        """
        pass
    
    def log_results(self, results: Dict[str, Any]) -> None:
        """
        Логирует результаты анализа.
        
        Args:
            results: Результаты анализа
        """
        for key, value in results.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    logger.log(self.log_level, f"{key}.{subkey}: {subvalue}")
            else:
                logger.log(self.log_level, f"{key}: {value}")
    
    def detect(self) -> Dict[str, Any]:
        """
        Обнаруживает узкие места.
        
        Returns:
            Dict[str, Any]: Результаты анализа
        """
        self.start_monitoring()
        try:
            return self.analyze()
        finally:
            self.stop_monitoring()


class QueryBottleneckDetector(BottleneckDetector):
    """
    Детектор узких мест в SQL-запросах.
    """
    
    def __init__(self, threshold: Optional[float] = 0.1, log_level: str = 'WARNING'):
        """
        Инициализирует детектор узких мест в SQL-запросах.
        
        Args:
            threshold: Пороговое значение времени выполнения запроса в секундах
            log_level: Уровень логирования
        """
        super().__init__(threshold, log_level)
        self.queries_before = []
        self.queries_after = []
    
    def start_monitoring(self) -> None:
        """
        Начинает мониторинг SQL-запросов.
        """
        self.queries_before = list(connection.queries)
    
    def stop_monitoring(self) -> None:
        """
        Останавливает мониторинг SQL-запросов.
        """
        self.queries_after = list(connection.queries)
    
    def analyze(self) -> Dict[str, Any]:
        """
        Анализирует SQL-запросы.
        
        Returns:
            Dict[str, Any]: Результаты анализа
        """
        new_queries = self.queries_after[len(self.queries_before):]
        
        if not new_queries:
            return {'message': 'No queries executed during monitoring'}
        
        total_time = sum(float(query.get('time', 0)) for query in new_queries)
        slow_queries = [
            query for query in new_queries
            if float(query.get('time', 0)) > self.threshold
        ]
        
        results = {
            'total_queries': len(new_queries),
            'total_time': total_time,
            'avg_time': total_time / len(new_queries) if new_queries else 0,
            'slow_queries_count': len(slow_queries),
            'slow_queries': [
                {
                    'sql': query.get('sql'),
                    'time': float(query.get('time', 0)),
                }
                for query in slow_queries
            ]
        }
        
        self.log_results(results)
        return results
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Возвращает список медленных запросов.
        
        Returns:
            List[Dict[str, Any]]: Список медленных запросов
        """
        results = self.analyze()
        return results.get('slow_queries', [])
    
    def get_query_stats(self) -> Dict[str, float]:
        """
        Возвращает статистику по запросам.
        
        Returns:
            Dict[str, float]: Статистика по запросам
        """
        results = self.analyze()
        return {
            'total_queries': results.get('total_queries', 0),
            'total_time': results.get('total_time', 0),
            'avg_time': results.get('avg_time', 0),
            'slow_queries_count': results.get('slow_queries_count', 0),
        }


class MemoryBottleneckDetector(BottleneckDetector):
    """
    Детектор узких мест в использовании памяти.
    """
    
    def __init__(self, threshold: Optional[float] = 10 * 1024 * 1024, log_level: str = 'WARNING'):
        """
        Инициализирует детектор узких мест в использовании памяти.
        
        Args:
            threshold: Пороговое значение использования памяти в байтах (по умолчанию 10 МБ)
            log_level: Уровень логирования
        """
        super().__init__(threshold, log_level)
        self.snapshot_before = None
        self.snapshot_after = None
    
    def start_monitoring(self) -> None:
        """
        Начинает мониторинг использования памяти.
        """
        tracemalloc.start()
        self.snapshot_before = tracemalloc.take_snapshot()
    
    def stop_monitoring(self) -> None:
        """
        Останавливает мониторинг использования памяти.
        """
        self.snapshot_after = tracemalloc.take_snapshot()
        tracemalloc.stop()
    
    def analyze(self) -> Dict[str, Any]:
        """
        Анализирует использование памяти.
        
        Returns:
            Dict[str, Any]: Результаты анализа
        """
        if not self.snapshot_before or not self.snapshot_after:
            return {'message': 'No memory snapshots available'}
        
        top_stats = self.snapshot_after.compare_to(self.snapshot_before, 'lineno')
        
        total_memory = sum(stat.size_diff for stat in top_stats)
        memory_leaks = [
            stat for stat in top_stats
            if stat.size_diff > self.threshold
        ]
        
        results = {
            'total_memory_diff': total_memory,
            'memory_leaks_count': len(memory_leaks),
            'memory_leaks': [
                {
                    'file': str(stat.traceback.frame.filename),
                    'line': stat.traceback.frame.lineno,
                    'size': stat.size_diff,
                    'count': stat.count_diff,
                }
                for stat in memory_leaks
            ]
        }
        
        self.log_results(results)
        return results
    
    def get_memory_leaks(self) -> List[Dict[str, Any]]:
        """
        Возвращает список утечек памяти.
        
        Returns:
            List[Dict[str, Any]]: Список утечек памяти
        """
        results = self.analyze()
        return results.get('memory_leaks', [])
    
    def get_memory_stats(self) -> Dict[str, float]:
        """
        Возвращает статистику по использованию памяти.
        
        Returns:
            Dict[str, float]: Статистика по использованию памяти
        """
        results = self.analyze()
        return {
            'total_memory_diff': results.get('total_memory_diff', 0),
            'memory_leaks_count': results.get('memory_leaks_count', 0),
        }


class TimeBottleneckDetector(BottleneckDetector):
    """
    Детектор узких мест по времени выполнения.
    """
    
    def __init__(self, threshold: Optional[float] = 1.0, log_level: str = 'WARNING'):
        """
        Инициализирует детектор узких мест по времени выполнения.
        
        Args:
            threshold: Пороговое значение времени выполнения в секундах
            log_level: Уровень логирования
        """
        super().__init__(threshold, log_level)
        self.start_time = None
        self.end_time = None
        self.function_times = {}
    
    def start_monitoring(self) -> None:
        """
        Начинает мониторинг времени выполнения.
        """
        self.start_time = time.time()
        self.function_times = {}
    
    def stop_monitoring(self) -> None:
        """
        Останавливает мониторинг времени выполнения.
        """
        self.end_time = time.time()
    
    def analyze(self) -> Dict[str, Any]:
        """
        Анализирует время выполнения.
        
        Returns:
            Dict[str, Any]: Результаты анализа
        """
        if not self.start_time or not self.end_time:
            return {'message': 'No time measurements available'}
        
        total_time = self.end_time - self.start_time
        slow_functions = {
            name: elapsed for name, elapsed in self.function_times.items()
            if elapsed > self.threshold
        }
        
        results = {
            'total_time': total_time,
            'slow_functions_count': len(slow_functions),
            'slow_functions': [
                {
                    'name': name,
                    'time': elapsed,
                }
                for name, elapsed in slow_functions.items()
            ]
        }
        
        self.log_results(results)
        return results
    
    def measure_function(self, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """
        Измеряет время выполнения функции.
        
        Args:
            func: Функция для измерения
            *args: Аргументы функции
            **kwargs: Именованные аргументы функции
            
        Returns:
            Tuple[Any, float]: Результат функции и время выполнения
        """
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        self.function_times[func.__name__] = elapsed
        
        return result, elapsed
    
    def get_slow_functions(self) -> List[Dict[str, Any]]:
        """
        Возвращает список медленных функций.
        
        Returns:
            List[Dict[str, Any]]: Список медленных функций
        """
        results = self.analyze()
        return results.get('slow_functions', [])
    
    def get_time_stats(self) -> Dict[str, float]:
        """
        Возвращает статистику по времени выполнения.
        
        Returns:
            Dict[str, float]: Статистика по времени выполнения
        """
        results = self.analyze()
        return {
            'total_time': results.get('total_time', 0),
            'slow_functions_count': results.get('slow_functions_count', 0),
        }

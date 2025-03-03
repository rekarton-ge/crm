"""
Модуль для оптимизации производительности приложения.

Этот модуль предоставляет инструменты для анализа и оптимизации производительности приложения.
"""

from core.performance.bottleneck_detector import (
    BottleneckDetector, QueryBottleneckDetector, MemoryBottleneckDetector
)
from core.performance.decorators import (
    profile_function, profile_query, cache_result, measure_time
)
from core.performance.query_optimizer import (
    QueryOptimizer, optimize_queryset, analyze_query_plan
)

__all__ = [
    # Детекторы узких мест
    'BottleneckDetector',
    'QueryBottleneckDetector',
    'MemoryBottleneckDetector',
    
    # Декораторы
    'profile_function',
    'profile_query',
    'cache_result',
    'measure_time',
    
    # Оптимизаторы запросов
    'QueryOptimizer',
    'optimize_queryset',
    'analyze_query_plan',
]

"""
Декораторы для профилирования и оптимизации производительности.

Этот модуль предоставляет декораторы для профилирования и оптимизации производительности функций и методов.
"""

import time
import functools
import logging
import cProfile
import pstats
import io
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast, Union

from django.core.cache import cache
from django.db import connection, reset_queries
from django.conf import settings

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def profile_function(output_file: Optional[str] = None) -> Callable[[F], F]:
    """
    Декоратор для профилирования функции с использованием cProfile.
    
    Args:
        output_file: Путь к файлу для сохранения результатов профилирования
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(20)  # Выводим топ-20 функций по времени выполнения
                
                if output_file:
                    ps.dump_stats(output_file)
                
                logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def profile_query(log_level: str = 'DEBUG') -> Callable[[F], F]:
    """
    Декоратор для профилирования SQL-запросов, выполняемых функцией.
    
    Args:
        log_level: Уровень логирования
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not settings.DEBUG:
                return func(*args, **kwargs)
            
            reset_queries()
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
            finally:
                end = time.time()
                
                queries = connection.queries
                num_queries = len(queries)
                total_time = sum(float(query.get('time', 0)) for query in queries)
                
                log_msg = (
                    f"{func.__name__} executed {num_queries} queries in {end - start:.3f}s "
                    f"(DB time: {total_time:.3f}s)"
                )
                
                if num_queries > 0:
                    log_msg += "\nQueries:"
                    for i, query in enumerate(queries, 1):
                        log_msg += f"\n{i}. {query.get('sql')} - {query.get('time')}s"
                
                getattr(logger, log_level.lower())(log_msg)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def cache_result(timeout: int = 60, key_prefix: str = '') -> Callable[[F], F]:
    """
    Декоратор для кеширования результатов функции.
    
    Args:
        timeout: Время жизни кеша в секундах
        key_prefix: Префикс для ключа кеша
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Формируем ключ кеша
            cache_key = f"{key_prefix}:{func.__module__}.{func.__name__}:"
            
            # Добавляем аргументы к ключу
            for arg in args:
                cache_key += f"{hash(str(arg))}:"
            
            # Добавляем именованные аргументы к ключу
            for key, value in sorted(kwargs.items()):
                cache_key += f"{key}:{hash(str(value))}:"
            
            # Проверяем наличие результата в кеше
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                return cached_result
            
            # Выполняем функцию и кешируем результат
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def measure_time(log_level: str = 'DEBUG') -> Callable[[F], F]:
    """
    Декоратор для измерения времени выполнения функции.
    
    Args:
        log_level: Уровень логирования
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
            finally:
                end = time.time()
                elapsed = end - start
                
                getattr(logger, log_level.lower())(
                    f"{func.__name__} executed in {elapsed:.3f}s"
                )
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, 
          exceptions: Union[Exception, List[Exception]] = Exception) -> Callable[[F], F]:
    """
    Декоратор для повторного выполнения функции при возникновении исключения.
    
    Args:
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками в секундах
        exceptions: Исключения, при которых нужно повторять попытки
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    
                    if attempts >= max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    
                    time.sleep(delay)
            
            # Этот код не должен выполняться, но добавлен для типизации
            return None
        
        return cast(F, wrapper)
    
    return decorator


def throttle(limit: int = 10, period: int = 60) -> Callable[[F], F]:
    """
    Декоратор для ограничения частоты вызовов функции.
    
    Args:
        limit: Максимальное количество вызовов
        period: Период времени в секундах
        
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: F) -> F:
        calls: Dict[str, List[float]] = {}
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Формируем ключ для отслеживания вызовов
            key = f"{func.__module__}.{func.__name__}"
            
            # Инициализируем список вызовов, если его нет
            if key not in calls:
                calls[key] = []
            
            # Получаем текущее время
            now = time.time()
            
            # Удаляем устаревшие вызовы
            calls[key] = [t for t in calls[key] if now - t < period]
            
            # Проверяем, не превышен ли лимит
            if len(calls[key]) >= limit:
                oldest_call = min(calls[key])
                wait_time = period - (now - oldest_call)
                
                logger.warning(
                    f"Function {func.__name__} throttled: {len(calls[key])} calls in {period}s. "
                    f"Try again in {wait_time:.1f}s."
                )
                
                raise Exception(
                    f"Function {func.__name__} throttled: too many calls. "
                    f"Try again in {wait_time:.1f}s."
                )
            
            # Добавляем текущий вызов
            calls[key].append(now)
            
            # Выполняем функцию
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator

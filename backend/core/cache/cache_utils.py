"""
Утилиты для работы с кэшем.

Этот модуль содержит функции и классы для работы с кэшем,
включая кэширование запросов, результатов функций и данных.
"""

import hashlib
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.core.cache import cache
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


def get_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Генерирует ключ кэша на основе префикса и аргументов.
    
    Args:
        prefix (str): Префикс ключа кэша.
        *args: Позиционные аргументы для включения в ключ кэша.
        **kwargs: Именованные аргументы для включения в ключ кэша.
    
    Returns:
        str: Ключ кэша.
    """
    # Преобразуем аргументы в строку
    args_str = str(args) if args else ""
    kwargs_str = str(sorted(kwargs.items())) if kwargs else ""
    
    # Создаем хеш из аргументов
    hash_str = hashlib.md5(f"{args_str}{kwargs_str}".encode()).hexdigest()
    
    return f"{prefix}:{hash_str}"


def cache_result(
    timeout: int = 3600,
    prefix: str = "cache_result",
    key_func: Optional[Callable] = None
) -> Callable:
    """
    Декоратор для кэширования результатов функции.
    
    Args:
        timeout (int, optional): Время жизни кэша в секундах. По умолчанию 3600 (1 час).
        prefix (str, optional): Префикс ключа кэша. По умолчанию "cache_result".
        key_func (Callable, optional): Функция для генерации ключа кэша.
            По умолчанию используется get_cache_key.
    
    Returns:
        Callable: Декорированная функция.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(func.__name__, *args, **kwargs)
            else:
                cache_key = get_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Пытаемся получить результат из кэша
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Если результата нет в кэше, вызываем функцию
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэше
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache(prefix: str, *args: Any, **kwargs: Any) -> bool:
    """
    Инвалидирует кэш с указанным префиксом и аргументами.
    
    Args:
        prefix (str): Префикс ключа кэша.
        *args: Позиционные аргументы для включения в ключ кэша.
        **kwargs: Именованные аргументы для включения в ключ кэша.
    
    Returns:
        bool: True, если кэш был инвалидирован, иначе False.
    """
    cache_key = get_cache_key(prefix, *args, **kwargs)
    return cache.delete(cache_key)


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Инвалидирует все ключи кэша, соответствующие указанному шаблону.
    
    Args:
        pattern (str): Шаблон ключа кэша.
    
    Returns:
        int: Количество инвалидированных ключей.
    """
    # Примечание: эта функция работает только с некоторыми бэкендами кэша,
    # такими как Redis. Для других бэкендов может потребоваться другая реализация.
    if hasattr(cache, 'delete_pattern'):
        return cache.delete_pattern(pattern)
    
    # Для бэкендов, не поддерживающих delete_pattern, можно использовать
    # обходное решение, но это может быть неэффективно
    logger.warning(f"Cache backend does not support delete_pattern: {pattern}")
    return 0


def cache_queryset(
    queryset: QuerySet,
    timeout: int = 3600,
    prefix: str = "queryset",
    include_query: bool = True
) -> List[Dict]:
    """
    Кэширует результаты QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet для кэширования.
        timeout (int, optional): Время жизни кэша в секундах. По умолчанию 3600 (1 час).
        prefix (str, optional): Префикс ключа кэша. По умолчанию "queryset".
        include_query (bool, optional): Включать ли запрос в ключ кэша. По умолчанию True.
    
    Returns:
        List[Dict]: Список словарей с данными из QuerySet.
    """
    # Генерируем ключ кэша
    query_str = str(queryset.query) if include_query else ""
    model_name = queryset.model.__name__
    cache_key = get_cache_key(f"{prefix}:{model_name}", query_str)
    
    # Пытаемся получить результат из кэша
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        logger.debug(f"Cache hit for queryset: {cache_key}")
        return cached_result
    
    # Если результата нет в кэше, выполняем запрос
    logger.debug(f"Cache miss for queryset: {cache_key}")
    
    # Преобразуем QuerySet в список словарей
    result = [
        {field.name: getattr(obj, field.name) for field in obj._meta.fields}
        for obj in queryset
    ]
    
    # Сохраняем результат в кэше
    cache.set(cache_key, result, timeout)
    
    return result


def cache_model_instance(
    instance: Model,
    timeout: int = 3600,
    prefix: str = "model",
    fields: Optional[List[str]] = None
) -> Dict:
    """
    Кэширует экземпляр модели.
    
    Args:
        instance (Model): Экземпляр модели для кэширования.
        timeout (int, optional): Время жизни кэша в секундах. По умолчанию 3600 (1 час).
        prefix (str, optional): Префикс ключа кэша. По умолчанию "model".
        fields (List[str], optional): Список полей для кэширования.
            По умолчанию кэшируются все поля.
    
    Returns:
        Dict: Словарь с данными экземпляра модели.
    """
    # Генерируем ключ кэша
    model_name = instance.__class__.__name__
    pk = instance.pk
    cache_key = get_cache_key(f"{prefix}:{model_name}", pk)
    
    # Пытаемся получить результат из кэша
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        logger.debug(f"Cache hit for model instance: {cache_key}")
        return cached_result
    
    # Если результата нет в кэше, создаем словарь с данными
    logger.debug(f"Cache miss for model instance: {cache_key}")
    
    if fields:
        result = {field: getattr(instance, field) for field in fields}
    else:
        result = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
    
    # Сохраняем результат в кэше
    cache.set(cache_key, result, timeout)
    
    return result


def cache_function(
    func: Callable,
    *args: Any,
    timeout: int = 3600,
    prefix: str = "function",
    **kwargs: Any
) -> Any:
    """
    Кэширует результат выполнения функции.
    
    Args:
        func (Callable): Функция для кэширования.
        *args: Позиционные аргументы функции.
        timeout (int, optional): Время жизни кэша в секундах. По умолчанию 3600 (1 час).
        prefix (str, optional): Префикс ключа кэша. По умолчанию "function".
        **kwargs: Именованные аргументы функции.
    
    Returns:
        Any: Результат выполнения функции.
    """
    # Генерируем ключ кэша
    cache_key = get_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
    
    # Пытаемся получить результат из кэша
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        logger.debug(f"Cache hit for function: {cache_key}")
        return cached_result
    
    # Если результата нет в кэше, вызываем функцию
    logger.debug(f"Cache miss for function: {cache_key}")
    result = func(*args, **kwargs)
    
    # Сохраняем результат в кэше
    cache.set(cache_key, result, timeout)
    
    return result


class CacheManager:
    """
    Менеджер кэша для управления кэшированием данных.
    """
    
    def __init__(self, prefix: str = "cache_manager", timeout: int = 3600):
        """
        Инициализирует менеджер кэша.
        
        Args:
            prefix (str, optional): Префикс ключа кэша. По умолчанию "cache_manager".
            timeout (int, optional): Время жизни кэша в секундах. По умолчанию 3600 (1 час).
        """
        self.prefix = prefix
        self.timeout = timeout
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение из кэша.
        
        Args:
            key (str): Ключ кэша.
            default (Any, optional): Значение по умолчанию. По умолчанию None.
        
        Returns:
            Any: Значение из кэша или значение по умолчанию.
        """
        cache_key = f"{self.prefix}:{key}"
        return cache.get(cache_key, default)
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Устанавливает значение в кэше.
        
        Args:
            key (str): Ключ кэша.
            value (Any): Значение для кэширования.
            timeout (int, optional): Время жизни кэша в секундах.
                По умолчанию используется timeout из конструктора.
        
        Returns:
            bool: True, если значение было установлено, иначе False.
        """
        cache_key = f"{self.prefix}:{key}"
        timeout = timeout if timeout is not None else self.timeout
        return cache.set(cache_key, value, timeout)
    
    def delete(self, key: str) -> bool:
        """
        Удаляет значение из кэша.
        
        Args:
            key (str): Ключ кэша.
        
        Returns:
            bool: True, если значение было удалено, иначе False.
        """
        cache_key = f"{self.prefix}:{key}"
        return cache.delete(cache_key)
    
    def clear(self) -> bool:
        """
        Очищает все значения с указанным префиксом.
        
        Returns:
            bool: True, если значения были очищены, иначе False.
        """
        return invalidate_cache_pattern(f"{self.prefix}:*") > 0
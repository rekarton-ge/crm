"""
Декораторы для кэширования.

Этот модуль содержит декораторы для кэширования результатов функций,
методов, свойств и ответов API.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from rest_framework.request import Request
from rest_framework.response import Response

from core.cache.cache_utils import get_cache_key

logger = logging.getLogger(__name__)


def cache_result(timeout: Optional[int] = None, key_prefix: Optional[str] = None,
                 key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кэширования результатов функции.
    
    Args:
        timeout (int, optional): Время жизни кэша в секундах.
            По умолчанию используется значение из настроек Django.
        key_prefix (str, optional): Префикс ключа кэша.
            По умолчанию используется имя функции.
        key_func (Callable, optional): Функция для генерации ключа кэша.
            По умолчанию используется get_cache_key.
    
    Returns:
        Callable: Декорированная функция.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Проверяем, включен ли кэш
            if not getattr(settings, 'USE_CACHE', True):
                return func(*args, **kwargs)
            
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(func.__name__, *args, **kwargs)
            else:
                prefix = key_prefix or f"func:{func.__name__}"
                cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Пытаемся получить результат из кэша
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Если результата нет в кэше, вызываем функцию
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэше
            cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT', 3600)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        
        return wrapper
    
    return decorator


def cache_method_result(timeout: Optional[int] = None, key_prefix: Optional[str] = None,
                        key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кэширования результатов метода класса.
    
    Отличается от cache_result тем, что исключает self из ключа кэша.
    
    Args:
        timeout (int, optional): Время жизни кэша в секундах.
            По умолчанию используется значение из настроек Django.
        key_prefix (str, optional): Префикс ключа кэша.
            По умолчанию используется имя класса и метода.
        key_func (Callable, optional): Функция для генерации ключа кэша.
            По умолчанию используется get_cache_key.
    
    Returns:
        Callable: Декорированный метод.
    """
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Проверяем, включен ли кэш
            if not getattr(settings, 'USE_CACHE', True):
                return method(self, *args, **kwargs)
            
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(method.__name__, self.__class__.__name__, *args, **kwargs)
            else:
                prefix = key_prefix or f"method:{self.__class__.__name__}:{method.__name__}"
                
                # Добавляем идентификатор объекта, если он есть
                if hasattr(self, 'pk') and self.pk:
                    prefix = f"{prefix}:{self.pk}"
                elif hasattr(self, 'id') and self.id:
                    prefix = f"{prefix}:{self.id}"
                
                cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Пытаемся получить результат из кэша
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Если результата нет в кэше, вызываем метод
            logger.debug(f"Cache miss for key: {cache_key}")
            result = method(self, *args, **kwargs)
            
            # Сохраняем результат в кэше
            cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT', 3600)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        
        return wrapper
    
    return decorator


def cache_property(timeout: Optional[int] = None, key_prefix: Optional[str] = None) -> Callable:
    """
    Декоратор для кэширования свойств класса.
    
    Args:
        timeout (int, optional): Время жизни кэша в секундах.
            По умолчанию используется значение из настроек Django.
        key_prefix (str, optional): Префикс ключа кэша.
            По умолчанию используется имя класса и свойства.
    
    Returns:
        Callable: Декорированное свойство.
    """
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self) -> Any:
            # Проверяем, включен ли кэш
            if not getattr(settings, 'USE_CACHE', True):
                return method(self)
            
            # Генерируем ключ кэша
            prefix = key_prefix or f"property:{self.__class__.__name__}:{method.__name__}"
            
            # Добавляем идентификатор объекта, если он есть
            if hasattr(self, 'pk') and self.pk:
                prefix = f"{prefix}:{self.pk}"
            elif hasattr(self, 'id') and self.id:
                prefix = f"{prefix}:{self.id}"
            
            cache_key = get_cache_key(prefix)
            
            # Пытаемся получить результат из кэша
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Если результата нет в кэше, вызываем метод
            logger.debug(f"Cache miss for key: {cache_key}")
            result = method(self)
            
            # Сохраняем результат в кэше
            cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT', 3600)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        
        return property(wrapper)
    
    return decorator


def default_cache_key_func(view_instance, request, *args, **kwargs):
    """
    Функция по умолчанию для генерации ключа кеша для декоратора cache_response.
    
    Args:
        view_instance: Экземпляр представления.
        request: HTTP-запрос.
        *args: Позиционные аргументы представления.
        **kwargs: Именованные аргументы представления.
    
    Returns:
        str: Ключ кеша.
    """
    # Создаем ключ на основе URL, метода и параметров запроса
    url = request.get_full_path()
    method = request.method
    
    # Добавляем информацию о пользователе, если он аутентифицирован
    user_id = request.user.pk if request.user and request.user.is_authenticated else 'anonymous'
    
    # Создаем префикс с информацией о представлении и пользователе
    prefix = f"response:{view_instance.__class__.__name__}:{user_id}:{method}"
    
    # Используем функцию get_cache_key для генерации хеша
    return get_cache_key(prefix, url, request.GET)


def cache_response(timeout: Optional[int] = None, key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кеширования ответа представления.
    
    Args:
        timeout: Время жизни кеша в секундах. По умолчанию используется CACHE_TIMEOUT из настроек.
        key_func: Функция для генерации ключа кеша. По умолчанию используется default_cache_key_func.
    
    Returns:
        Декоратор для кеширования ответа представления.
    """
    def decorator(view_method: Callable) -> Callable:
        @functools.wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            # Если кеширование отключено, просто вызываем метод представления
            if getattr(settings, 'DISABLE_CACHE', False):
                return view_method(self, request, *args, **kwargs)
            
            # Получаем ключ кеша
            key_function = key_func or default_cache_key_func
            cache_key = key_function(self, request, *args, **kwargs)
            
            # Пытаемся получить результат из кэша
            cached_data = cache.get(cache_key)
            
            if cached_data is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                # Восстанавливаем Response из кешированных данных
                data, status = cached_data
                return Response(data=data, status=status)
            
            # Если результата нет в кэше, вызываем метод представления
            logger.debug(f"Cache miss for key: {cache_key}")
            response = view_method(self, request, *args, **kwargs)
            
            # Сохраняем результат в кэше, только если это успешный ответ
            if 200 <= response.status_code < 300:
                # Кешируем только данные и статус-код, а не весь объект Response
                cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT', 3600)
                cache.set(cache_key, (response.data, response.status_code), cache_timeout)
            
            return response
        
        return wrapper
    
    return decorator


def invalidate_cache_on_save(model_or_models: Union[type, list, tuple], key_prefix: Optional[str] = None) -> Callable:
    """
    Декоратор для инвалидации кэша при сохранении модели.
    
    Args:
        model_or_models (Union[type, list, tuple]): Модель или список моделей,
            при сохранении которых нужно инвалидировать кэш.
        key_prefix (str, optional): Префикс ключа кэша для инвалидации.
            По умолчанию инвалидируются все ключи, связанные с моделью.
    
    Returns:
        Callable: Декорированный метод.
    """
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Выполняем метод
            result = method(*args, **kwargs)
            
            # Инвалидируем кэш
            models = model_or_models if isinstance(model_or_models, (list, tuple)) else [model_or_models]
            
            for model in models:
                model_name = model.__name__
                
                if key_prefix:
                    # Инвалидируем кэш с указанным префиксом
                    pattern = f"{key_prefix}*"
                else:
                    # Инвалидируем все ключи, связанные с моделью
                    pattern = f"*{model_name}*"
                
                # Инвалидируем кэш
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern(pattern)
                    logger.debug(f"Invalidated cache with pattern: {pattern}")
                else:
                    logger.warning(f"Cache backend does not support delete_pattern: {pattern}")
            
            return result
        
        return wrapper
    
    return decorator


def disable_cache_for_user(user_check_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для отключения кэширования для определенных пользователей.
    
    Args:
        user_check_func (Callable, optional): Функция для проверки пользователя.
            По умолчанию кэширование отключается для суперпользователей и персонала.
    
    Returns:
        Callable: Декорированный метод представления.
    """
    def default_user_check(user):
        """
        Проверяет, является ли пользователь суперпользователем или персоналом.
        
        Args:
            user: Пользователь для проверки.
        
        Returns:
            bool: True, если кэширование нужно отключить, иначе False.
        """
        return user and user.is_authenticated and (user.is_superuser or user.is_staff)
    
    check_func = user_check_func or default_user_check
    
    def decorator(view_method: Callable) -> Callable:
        @functools.wraps(view_method)
        def wrapper(self, request: Union[HttpRequest, Request], *args: Any, **kwargs: Any) -> Response:
            # Проверяем пользователя
            if check_func(request.user):
                # Отключаем кэширование для этого запроса
                with override_cache_settings(False):
                    return view_method(self, request, *args, **kwargs)
            
            # Для остальных пользователей используем обычное поведение
            return view_method(self, request, *args, **kwargs)
        
        return wrapper
    
    return decorator


class override_cache_settings:
    """
    Контекстный менеджер для временного изменения настроек кэширования.
    
    Args:
        use_cache (bool): Включить или отключить кэширование.
        timeout (int, optional): Время жизни кэша в секундах.
    """
    
    def __init__(self, use_cache: bool, timeout: Optional[int] = None):
        self.use_cache = use_cache
        self.timeout = timeout
        self.old_use_cache = None
        self.old_timeout = None
    
    def __enter__(self):
        # Сохраняем текущие настройки
        self.old_use_cache = getattr(settings, 'USE_CACHE', True)
        self.old_timeout = getattr(settings, 'CACHE_TIMEOUT', None)
        
        # Устанавливаем новые настройки
        settings.USE_CACHE = self.use_cache
        
        if self.timeout is not None:
            settings.CACHE_TIMEOUT = self.timeout
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Восстанавливаем старые настройки
        settings.USE_CACHE = self.old_use_cache
        
        if self.old_timeout is not None:
            settings.CACHE_TIMEOUT = self.old_timeout
        elif hasattr(settings, 'CACHE_TIMEOUT'):
            delattr(settings, 'CACHE_TIMEOUT')
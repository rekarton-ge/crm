"""
Декораторы для кэширования.

Этот модуль содержит декораторы для кэширования результатов функций и методов,
а также ответов API представлений.
"""

import functools
import hashlib
import inspect
import json
from typing import Any, Callable, Dict, Optional, Union

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from rest_framework.request import Request
from rest_framework.response import Response

from core.cache.cache_utils import generate_cache_key, is_cache_enabled


def cache_result(timeout: Optional[int] = None, key_prefix: Optional[str] = None,
                 key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кэширования результатов функции или метода.

    Args:
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        key_prefix: Префикс для ключа кэша
        key_func: Функция для генерации ключа кэша

    Returns:
        Callable: Декорированная функция

    Examples:
        ```python
        @cache_result(timeout=300, key_prefix='my_function')
        def my_function(arg1, arg2):
            # Выполнение сложных вычислений
            return result
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Проверяем, включен ли кэш
            if not is_cache_enabled():
                return func(*args, **kwargs)

            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                prefix = key_prefix or f"{func.__module__}.{func.__name__}"
                cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Проверяем, есть ли результат в кэше
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Вычисляем результат
            result = func(*args, **kwargs)

            # Сохраняем результат в кэш
            cache.set(cache_key, result, timeout=timeout)

            return result

        return wrapper

    return decorator


def cache_method_result(timeout: Optional[int] = None, key_prefix: Optional[str] = None,
                        key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кэширования результатов метода класса.

    Работает аналогично cache_result, но учитывает self при создании ключа кэша.

    Args:
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        key_prefix: Префикс для ключа кэша
        key_func: Функция для генерации ключа кэша

    Returns:
        Callable: Декорированный метод

    Examples:
        ```python
        class MyClass:
            @cache_method_result(timeout=300, key_prefix='my_method')
            def my_method(self, arg1, arg2):
                # Выполнение сложных вычислений
                return result
        ```
    """

    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Проверяем, включен ли кэш
            if not is_cache_enabled():
                return method(self, *args, **kwargs)

            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                # Используем класс и ID (если есть) объекта для создания уникального ключа
                obj_id = getattr(self, 'id', None) or getattr(self, 'pk', None) or id(self)
                prefix = key_prefix or f"{self.__class__.__module__}.{self.__class__.__name__}.{method.__name__}"
                cache_key = generate_cache_key(prefix, obj_id, *args, **kwargs)

            # Проверяем, есть ли результат в кэше
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Вычисляем результат
            result = method(self, *args, **kwargs)

            # Сохраняем результат в кэш
            cache.set(cache_key, result, timeout=timeout)

            return result

        return wrapper

    return decorator


def cache_property(timeout: Optional[int] = None, key_prefix: Optional[str] = None) -> Callable:
    """
    Декоратор для кэширования свойств класса.

    Кэширует значение свойства на указанное время.

    Args:
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        key_prefix: Префикс для ключа кэша

    Returns:
        Callable: Декорированное свойство

    Examples:
        ```python
        class MyClass:
            @property
            @cache_property(timeout=300, key_prefix='my_property')
            def my_property(self):
                # Вычисление сложного свойства
                return result
        ```
    """

    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self) -> Any:
            # Проверяем, включен ли кэш
            if not is_cache_enabled():
                return method(self)

            # Генерируем ключ кэша
            obj_id = getattr(self, 'id', None) or getattr(self, 'pk', None) or id(self)
            prefix = key_prefix or f"{self.__class__.__module__}.{self.__class__.__name__}.{method.__name__}"
            cache_key = generate_cache_key(prefix, obj_id)

            # Проверяем, есть ли результат в кэше
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Вычисляем результат
            result = method(self)

            # Сохраняем результат в кэш
            cache.set(cache_key, result, timeout=timeout)

            return result

        return wrapper

    return decorator


def cache_response(timeout: Optional[int] = None, key_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для кэширования ответов API представлений.

    Args:
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        key_func: Функция для генерации ключа кэша

    Returns:
        Callable: Декорированный метод представления

    Examples:
        ```python
        class MyViewSet(viewsets.ModelViewSet):
            @cache_response(timeout=300)
            def list(self, request, *args, **kwargs):
                # Стандартный метод list
                return super().list(request, *args, **kwargs)
        ```
    """

    def decorator(view_method: Callable) -> Callable:
        @functools.wraps(view_method)
        def wrapper(self, request: Union[HttpRequest, Request], *args: Any, **kwargs: Any) -> Response:
            # Проверяем, включен ли кэш
            if not is_cache_enabled():
                return view_method(self, request, *args, **kwargs)

            # Проверяем, является ли метод безопасным (GET, HEAD)
            if request.method not in ('GET', 'HEAD'):
                return view_method(self, request, *args, **kwargs)

            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(self, view_method, request, *args, **kwargs)
            else:
                # Создаем ключ на основе текущего пути, метода и параметров запроса
                path = request.path
                query_params = request.query_params if hasattr(request, 'query_params') else request.GET

                # Сортируем параметры запроса для обеспечения стабильного порядка
                sorted_params = sorted(query_params.items())
                params_str = json.dumps(sorted_params, sort_keys=True)

                # Создаем хеш для параметров
                params_hash = hashlib.md5(force_bytes(params_str)).hexdigest()

                prefix = f"{self.__class__.__module__}.{self.__class__.__name__}.{view_method.__name__}"
                cache_key = f"{prefix}_{path}_{params_hash}"

            # Проверяем, есть ли ответ в кэше
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Получаем ответ
            response = view_method(self, request, *args, **kwargs)

            # Сохраняем ответ в кэш
            if response.status_code == 200:  # Кэшируем только успешные ответы
                cache.set(cache_key, response, timeout=timeout)

            return response

        return wrapper

    return decorator


def invalidate_cache_on_save(model_or_models: Union[type, list, tuple], key_prefix: Optional[str] = None) -> Callable:
    """
    Декоратор для инвалидации кэша при сохранении модели.

    Используется для методов, которые изменяют модель и требуют инвалидации кэша.

    Args:
        model_or_models: Модель или список моделей, кэш которых нужно инвалидировать
        key_prefix: Префикс ключа кэша для инвалидации

    Returns:
        Callable: Декорированный метод

    Examples:
        ```python
        class MyView(APIView):
            @invalidate_cache_on_save(MyModel, key_prefix='my_cached_view')
            def post(self, request):
                # Изменение модели
                return Response(...)
        ```
    """

    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Выполняем метод
            result = method(*args, **kwargs)

            # Преобразуем модель или список моделей в список
            models = model_or_models
            if not isinstance(models, (list, tuple)):
                models = [models]

            # Инвалидируем кэш для каждой модели
            for model in models:
                prefix = key_prefix or f"{model.__module__}.{model.__name__}"
                # Для Redis можно использовать шаблоны
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern(f"{prefix}*")
                # Для других бэкендов - ключевые кэши по отдельности
                else:
                    # Здесь можно определить и инвалидировать конкретные ключи
                    # Например, кэш для list, retrieve и т.д.
                    cache.delete(f"{prefix}_list")

            return result

        return wrapper

    return decorator


def disable_cache_for_user(user_check_func: Optional[Callable] = None) -> Callable:
    """
    Декоратор для отключения кэширования для определенных пользователей.

    Args:
        user_check_func: Функция, проверяющая, нужно ли отключить кэш для пользователя

    Returns:
        Callable: Декорированный метод представления

    Examples:
        ```python
        def is_staff(user):
            return user.is_staff

        class MyViewSet(viewsets.ModelViewSet):
            @cache_response(timeout=300)
            @disable_cache_for_user(user_check_func=is_staff)
            def list(self, request, *args, **kwargs):
                # Для staff пользователей кэш будет отключен
                return super().list(request, *args, **kwargs)
        ```
    """

    def decorator(view_method: Callable) -> Callable:
        @functools.wraps(view_method)
        def wrapper(self, request: Union[HttpRequest, Request], *args: Any, **kwargs: Any) -> Response:
            # Проверяем пользователя
            user = getattr(request, 'user', None)
            if user and user_check_func and user_check_func(user):
                # Временно отключаем кэш для этого запроса
                original_timeout = getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 0)
                setattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 0)

                try:
                    return view_method(self, request, *args, **kwargs)
                finally:
                    # Восстанавливаем настройки кэша
                    setattr(settings, 'CACHE_MIDDLEWARE_SECONDS', original_timeout)

            return view_method(self, request, *args, **kwargs)

        return wrapper

    return decorator
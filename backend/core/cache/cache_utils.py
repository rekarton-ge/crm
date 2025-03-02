"""
Утилиты для работы с кэшем.

Этот модуль содержит вспомогательные функции и классы для работы с кэшем,
включая генерацию ключей кэша, инвалидацию кэша и другие общие операции.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Dict, List, Optional, Union, Callable

from django.conf import settings
from django.core.cache import cache
from django.db.models import Model
from django.utils.encoding import force_bytes


def generate_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Генерирует ключ кэша на основе префикса и аргументов.

    Args:
        prefix: Префикс ключа кэша
        *args: Аргументы для включения в ключ кэша
        **kwargs: Именованные аргументы для включения в ключ кэша

    Returns:
        str: Сгенерированный ключ кэша
    """
    # Создаем хеш всех аргументов
    key_parts = [prefix]

    # Добавляем аргументы
    for arg in args:
        if isinstance(arg, Model):
            # Для моделей используем имя класса и первичный ключ
            key_parts.append(f"{arg.__class__.__name__}_{arg.pk}")
        else:
            key_parts.append(str(arg))

    # Добавляем именованные аргументы
    if kwargs:
        # Сортируем для обеспечения стабильного порядка
        sorted_kwargs = sorted(kwargs.items())
        for key, value in sorted_kwargs:
            if isinstance(value, Model):
                # Для моделей используем имя класса и первичный ключ
                key_parts.append(f"{key}_{value.__class__.__name__}_{value.pk}")
            else:
                key_parts.append(f"{key}_{value}")

    # Объединяем все части
    key = '_'.join(key_parts)

    # Если ключ слишком длинный, используем хеш
    if len(key) > 250:
        key_hash = hashlib.md5(force_bytes(key)).hexdigest()
        key = f"{prefix}_{key_hash}"

    return key


def cache_get_or_set(key: str, default_func: Callable, timeout: Optional[int] = None) -> Any:
    """
    Получает значение из кэша или устанавливает его, если оно отсутствует.

    Аналог встроенного cache.get_or_set(), но с дополнительными опциями.

    Args:
        key: Ключ кэша
        default_func: Функция для получения значения, если оно отсутствует в кэше
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию

    Returns:
        Any: Значение из кэша или результат default_func
    """
    value = cache.get(key)
    if value is None:
        value = default_func()
        # Устанавливаем значение в кэш
        if value is not None:
            cache.set(key, value, timeout=timeout)
    return value


def invalidate_cache_keys(keys: List[str]) -> None:
    """
    Инвалидирует указанные ключи кэша.

    Args:
        keys: Список ключей кэша для инвалидации
    """
    for key in keys:
        cache.delete(key)


def invalidate_cache_prefix(prefix: str) -> None:
    """
    Инвалидирует все ключи кэша с указанным префиксом.

    Примечание: Этот метод эффективен только если бэкенд кэша поддерживает
    фильтрацию по префиксу, как Redis.

    Args:
        prefix: Префикс ключей кэша для инвалидации
    """
    if hasattr(cache, 'delete_pattern'):
        # Для Redis-подобных бэкендов, которые поддерживают шаблоны
        cache.delete_pattern(f"{prefix}*")
    else:
        # Для других бэкендов нельзя эффективно инвалидировать по префиксу
        # Можно использовать версионирование ключей как альтернативу
        pass


def get_model_cache_key(model_instance: Model, prefix: Optional[str] = None) -> str:
    """
    Генерирует ключ кэша для модели на основе ее класса и первичного ключа.

    Args:
        model_instance: Экземпляр модели
        prefix: Дополнительный префикс для ключа кэша

    Returns:
        str: Ключ кэша для модели
    """
    model_name = model_instance.__class__.__name__.lower()
    if prefix:
        return f"{prefix}_{model_name}_{model_instance.pk}"
    else:
        return f"{model_name}_{model_instance.pk}"


def invalidate_model_cache(model_instance: Model, prefix: Optional[str] = None) -> None:
    """
    Инвалидирует кэш для указанной модели.

    Args:
        model_instance: Экземпляр модели
        prefix: Дополнительный префикс для ключа кэша
    """
    key = get_model_cache_key(model_instance, prefix)
    cache.delete(key)


def get_queryset_cache_key(model_class: type, query_kwargs: Dict[str, Any], prefix: Optional[str] = None) -> str:
    """
    Генерирует ключ кэша для QuerySet на основе модели и параметров запроса.

    Args:
        model_class: Класс модели
        query_kwargs: Параметры запроса к QuerySet
        prefix: Дополнительный префикс для ключа кэша

    Returns:
        str: Ключ кэша для QuerySet
    """
    model_name = model_class.__name__.lower()

    # Создаем упорядоченное представление параметров запроса
    sorted_kwargs = sorted(query_kwargs.items())
    kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)

    # Создаем хеш параметров запроса
    query_hash = hashlib.md5(force_bytes(kwargs_str)).hexdigest()

    if prefix:
        return f"{prefix}_{model_name}_queryset_{query_hash}"
    else:
        return f"{model_name}_queryset_{query_hash}"


def cache_queryset(queryset, timeout: Optional[int] = None, prefix: Optional[str] = None) -> list:
    """
    Кэширует результаты QuerySet.

    Args:
        queryset: QuerySet для кэширования
        timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        prefix: Дополнительный префикс для ключа кэша

    Returns:
        list: Результаты QuerySet
    """
    model_class = queryset.model
    query_kwargs = queryset.query.__str__()

    key = get_queryset_cache_key(model_class, {'query': query_kwargs}, prefix)

    return cache_get_or_set(key, lambda: list(queryset), timeout)


def is_cache_enabled() -> bool:
    """
    Проверяет, включен ли кэш в настройках проекта.

    Returns:
        bool: True, если кэш включен, иначе False
    """
    cache_backend = getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', '')

    # Проверяем, что бэкенд кэша не является "dummy" (отключенным)
    if 'dummy' in cache_backend.lower():
        return False

    # Проверяем, что кэш включен в настройках
    return getattr(settings, 'USE_CACHE', True)


class CacheManager:
    """
    Менеджер кэша для управления кэшем связанным с определенным объектом.

    Обеспечивает удобный интерфейс для работы с кэшем в контексте
    определенного объекта или группы объектов.
    """

    def __init__(self, prefix: str):
        """
        Инициализирует менеджер кэша с указанным префиксом.

        Args:
            prefix: Префикс для всех ключей кэша, управляемых этим менеджером
        """
        self.prefix = prefix

    def get_key(self, *args: Any, **kwargs: Any) -> str:
        """
        Генерирует ключ кэша с префиксом менеджера.

        Args:
            *args: Аргументы для включения в ключ кэша
            **kwargs: Именованные аргументы для включения в ключ кэша

        Returns:
            str: Сгенерированный ключ кэша
        """
        return generate_cache_key(self.prefix, *args, **kwargs)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение из кэша по ключу.

        Args:
            key: Ключ кэша (без префикса)
            default: Значение по умолчанию, если ключ отсутствует

        Returns:
            Any: Значение из кэша или значение по умолчанию
        """
        full_key = self.get_key(key)
        return cache.get(full_key, default)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """
        Устанавливает значение в кэш по ключу.

        Args:
            key: Ключ кэша (без префикса)
            value: Значение для сохранения в кэше
            timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию
        """
        full_key = self.get_key(key)
        cache.set(full_key, value, timeout=timeout)

    def delete(self, key: str) -> None:
        """
        Удаляет значение из кэша по ключу.

        Args:
            key: Ключ кэша (без префикса)
        """
        full_key = self.get_key(key)
        cache.delete(full_key)

    def get_or_set(self, key: str, default_func: Callable, timeout: Optional[int] = None) -> Any:
        """
        Получает значение из кэша или устанавливает его, если оно отсутствует.

        Args:
            key: Ключ кэша (без префикса)
            default_func: Функция для получения значения, если оно отсутствует в кэше
            timeout: Время жизни кэша в секундах, если None, используется значение по умолчанию

        Returns:
            Any: Значение из кэша или результат default_func
        """
        full_key = self.get_key(key)
        return cache_get_or_set(full_key, default_func, timeout)

    def clear_all(self) -> None:
        """
        Очищает все ключи кэша с префиксом менеджера.
        """
        invalidate_cache_prefix(self.prefix)
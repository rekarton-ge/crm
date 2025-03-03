"""
Бэкенды кэширования.

Этот модуль содержит расширенные бэкенды кэширования для Django.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union

from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
from django.core.cache.backends.locmem import LocMemCache
from django.core.cache.backends.redis import RedisCache

logger = logging.getLogger(__name__)


class PrefixedCache(BaseCache):
    """
    Бэкенд кэширования, который добавляет префикс к ключам.
    
    Это обертка вокруг другого бэкенда кэширования, которая добавляет
    префикс к ключам перед их передачей в базовый бэкенд.
    """
    
    def __init__(self, backend: BaseCache, prefix: str, **kwargs):
        """
        Инициализирует бэкенд кэширования с префиксом.
        
        Args:
            backend (BaseCache): Базовый бэкенд кэширования.
            prefix (str): Префикс для ключей.
            **kwargs: Дополнительные аргументы для базового бэкенда.
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.prefix = prefix
    
    def _get_prefixed_key(self, key: str) -> str:
        """
        Добавляет префикс к ключу.
        
        Args:
            key (str): Ключ.
        
        Returns:
            str: Ключ с префиксом.
        """
        return f"{self.prefix}:{key}"
    
    def add(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> bool:
        """
        Добавляет значение в кэш, если ключ не существует.
        
        Args:
            key (str): Ключ.
            value (Any): Значение.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        
        Returns:
            bool: True, если значение было добавлено, иначе False.
        """
        prefixed_key = self._get_prefixed_key(key)
        return self.backend.add(prefixed_key, value, timeout, version)
    
    def get(self, key: str, default: Any = None, version: Optional[int] = None) -> Any:
        """
        Получает значение из кэша.
        
        Args:
            key (str): Ключ.
            default (Any, optional): Значение по умолчанию.
            version (int, optional): Версия кэша.
        
        Returns:
            Any: Значение из кэша или значение по умолчанию.
        """
        prefixed_key = self._get_prefixed_key(key)
        return self.backend.get(prefixed_key, default, version)
    
    def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        """
        Устанавливает значение в кэш.
        
        Args:
            key (str): Ключ.
            value (Any): Значение.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        """
        prefixed_key = self._get_prefixed_key(key)
        self.backend.set(prefixed_key, value, timeout, version)
    
    def delete(self, key: str, version: Optional[int] = None) -> None:
        """
        Удаляет значение из кэша.
        
        Args:
            key (str): Ключ.
            version (int, optional): Версия кэша.
        """
        prefixed_key = self._get_prefixed_key(key)
        self.backend.delete(prefixed_key, version)
    
    def clear(self) -> None:
        """
        Очищает кэш.
        """
        self.backend.clear()
    
    def get_many(self, keys: List[str], version: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает несколько значений из кэша.
        
        Args:
            keys (List[str]): Список ключей.
            version (int, optional): Версия кэша.
        
        Returns:
            Dict[str, Any]: Словарь с ключами и значениями.
        """
        prefixed_keys = [self._get_prefixed_key(key) for key in keys]
        result = self.backend.get_many(prefixed_keys, version)
        
        # Удаляем префикс из ключей в результате
        return {key[len(self.prefix) + 1:]: value for key, value in result.items()}
    
    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        """
        Устанавливает несколько значений в кэш.
        
        Args:
            data (Dict[str, Any]): Словарь с ключами и значениями.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        """
        prefixed_data = {self._get_prefixed_key(key): value for key, value in data.items()}
        self.backend.set_many(prefixed_data, timeout, version)
    
    def delete_many(self, keys: List[str], version: Optional[int] = None) -> None:
        """
        Удаляет несколько значений из кэша.
        
        Args:
            keys (List[str]): Список ключей.
            version (int, optional): Версия кэша.
        """
        prefixed_keys = [self._get_prefixed_key(key) for key in keys]
        self.backend.delete_many(prefixed_keys, version)
    
    def incr(self, key: str, delta: int = 1, version: Optional[int] = None) -> int:
        """
        Увеличивает значение в кэше.
        
        Args:
            key (str): Ключ.
            delta (int, optional): Значение для увеличения.
            version (int, optional): Версия кэша.
        
        Returns:
            int: Новое значение.
        """
        prefixed_key = self._get_prefixed_key(key)
        return self.backend.incr(prefixed_key, delta, version)
    
    def decr(self, key: str, delta: int = 1, version: Optional[int] = None) -> int:
        """
        Уменьшает значение в кэше.
        
        Args:
            key (str): Ключ.
            delta (int, optional): Значение для уменьшения.
            version (int, optional): Версия кэша.
        
        Returns:
            int: Новое значение.
        """
        prefixed_key = self._get_prefixed_key(key)
        return self.backend.decr(prefixed_key, delta, version)
    
    def has_key(self, key: str, version: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли ключ в кэше.
        
        Args:
            key (str): Ключ.
            version (int, optional): Версия кэша.
        
        Returns:
            bool: True, если ключ существует, иначе False.
        """
        prefixed_key = self._get_prefixed_key(key)
        return self.backend.has_key(prefixed_key, version)


class PatternRedisCacheClient:
    """
    Клиент для Redis с поддержкой шаблонов ключей.
    
    Расширяет стандартный клиент Redis для поддержки удаления ключей по шаблону.
    """
    
    def __init__(self, client):
        """
        Инициализирует клиент Redis.
        
        Args:
            client: Клиент Redis.
        """
        self.client = client
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Удаляет ключи, соответствующие шаблону.
        
        Args:
            pattern (str): Шаблон ключей.
        
        Returns:
            int: Количество удаленных ключей.
        """
        keys = self.client.keys(pattern)
        if keys:
            return self.client.delete(*keys)
        return 0


class PatternRedisCache(RedisCache):
    """
    Бэкенд кэширования Redis с поддержкой шаблонов ключей.
    
    Расширяет стандартный бэкенд Redis для поддержки удаления ключей по шаблону.
    """
    
    def __init__(self, server: str, params: Dict[str, Any]):
        """
        Инициализирует бэкенд кэширования Redis.
        
        Args:
            server (str): Адрес сервера Redis.
            params (Dict[str, Any]): Параметры подключения.
        """
        super().__init__(server, params)
        self._client = PatternRedisCacheClient(self._client)
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Удаляет ключи, соответствующие шаблону.
        
        Args:
            pattern (str): Шаблон ключей.
        
        Returns:
            int: Количество удаленных ключей.
        """
        pattern = self.make_key(pattern)
        return self._client.delete_pattern(pattern)


class PatternLocMemCache(LocMemCache):
    """
    Бэкенд кэширования LocMem с поддержкой шаблонов ключей.
    
    Расширяет стандартный бэкенд LocMem для поддержки удаления ключей по шаблону.
    """
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Удаляет ключи, соответствующие шаблону.
        
        Args:
            pattern (str): Шаблон ключей.
        
        Returns:
            int: Количество удаленных ключей.
        """
        pattern = self.make_key(pattern)
        pattern_regex = re.compile(pattern.replace('*', '.*'))
        
        with self._lock:
            keys_to_delete = [key for key in self._cache.keys() if pattern_regex.match(key)]
            count = len(keys_to_delete)
            
            for key in keys_to_delete:
                self._cache.pop(key, None)
            
            return count


class TieredCache(BaseCache):
    """
    Многоуровневый бэкенд кэширования.
    
    Использует несколько бэкендов кэширования в порядке приоритета.
    """
    
    def __init__(self, caches: List[BaseCache], **kwargs):
        """
        Инициализирует многоуровневый бэкенд кэширования.
        
        Args:
            caches (List[BaseCache]): Список бэкендов кэширования.
            **kwargs: Дополнительные аргументы.
        """
        super().__init__(**kwargs)
        self.caches = caches
    
    def add(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> bool:
        """
        Добавляет значение в кэш, если ключ не существует.
        
        Args:
            key (str): Ключ.
            value (Any): Значение.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        
        Returns:
            bool: True, если значение было добавлено, иначе False.
        """
        # Проверяем, существует ли ключ в любом из кэшей
        for cache in self.caches:
            if cache.has_key(key, version):
                return False
        
        # Добавляем значение во все кэши
        for cache in self.caches:
            cache.add(key, value, timeout, version)
        
        return True
    
    def get(self, key: str, default: Any = None, version: Optional[int] = None) -> Any:
        """
        Получает значение из кэша.
        
        Args:
            key (str): Ключ.
            default (Any, optional): Значение по умолчанию.
            version (int, optional): Версия кэша.
        
        Returns:
            Any: Значение из кэша или значение по умолчанию.
        """
        # Пытаемся получить значение из кэшей в порядке приоритета
        for i, cache in enumerate(self.caches):
            value = cache.get(key, None, version)
            
            if value is not None:
                # Если значение найдено в кэше с низким приоритетом,
                # добавляем его в кэши с более высоким приоритетом
                for j in range(i):
                    self.caches[j].set(key, value, self.default_timeout, version)
                
                return value
        
        return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        """
        Устанавливает значение в кэш.
        
        Args:
            key (str): Ключ.
            value (Any): Значение.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        """
        # Устанавливаем значение во все кэши
        for cache in self.caches:
            cache.set(key, value, timeout, version)
    
    def delete(self, key: str, version: Optional[int] = None) -> None:
        """
        Удаляет значение из кэша.
        
        Args:
            key (str): Ключ.
            version (int, optional): Версия кэша.
        """
        # Удаляем значение из всех кэшей
        for cache in self.caches:
            cache.delete(key, version)
    
    def clear(self) -> None:
        """
        Очищает кэш.
        """
        # Очищаем все кэши
        for cache in self.caches:
            cache.clear()
    
    def get_many(self, keys: List[str], version: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает несколько значений из кэша.
        
        Args:
            keys (List[str]): Список ключей.
            version (int, optional): Версия кэша.
        
        Returns:
            Dict[str, Any]: Словарь с ключами и значениями.
        """
        # Создаем словарь для результатов
        result = {}
        
        # Создаем множество ключей, которые еще не найдены
        remaining_keys = set(keys)
        
        # Пытаемся получить значения из кэшей в порядке приоритета
        for i, cache in enumerate(self.caches):
            # Получаем значения для оставшихся ключей
            values = cache.get_many(list(remaining_keys), version)
            
            # Добавляем найденные значения в результат
            result.update(values)
            
            # Обновляем множество оставшихся ключей
            remaining_keys -= set(values.keys())
            
            # Если все ключи найдены, выходим из цикла
            if not remaining_keys:
                break
            
            # Если найдены какие-то значения, добавляем их в кэши с более высоким приоритетом
            if values and i > 0:
                for j in range(i):
                    self.caches[j].set_many(values, self.default_timeout, version)
        
        return result
    
    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = DEFAULT_TIMEOUT, version: Optional[int] = None) -> None:
        """
        Устанавливает несколько значений в кэш.
        
        Args:
            data (Dict[str, Any]): Словарь с ключами и значениями.
            timeout (int, optional): Время жизни кэша в секундах.
            version (int, optional): Версия кэша.
        """
        # Устанавливаем значения во все кэши
        for cache in self.caches:
            cache.set_many(data, timeout, version)
    
    def delete_many(self, keys: List[str], version: Optional[int] = None) -> None:
        """
        Удаляет несколько значений из кэша.
        
        Args:
            keys (List[str]): Список ключей.
            version (int, optional): Версия кэша.
        """
        # Удаляем значения из всех кэшей
        for cache in self.caches:
            cache.delete_many(keys, version)
    
    def incr(self, key: str, delta: int = 1, version: Optional[int] = None) -> int:
        """
        Увеличивает значение в кэше.
        
        Args:
            key (str): Ключ.
            delta (int, optional): Значение для увеличения.
            version (int, optional): Версия кэша.
        
        Returns:
            int: Новое значение.
        """
        # Увеличиваем значение в первом кэше
        value = self.caches[0].incr(key, delta, version)
        
        # Обновляем значение в остальных кэшах
        for cache in self.caches[1:]:
            cache.set(key, value, self.default_timeout, version)
        
        return value
    
    def decr(self, key: str, delta: int = 1, version: Optional[int] = None) -> int:
        """
        Уменьшает значение в кэше.
        
        Args:
            key (str): Ключ.
            delta (int, optional): Значение для уменьшения.
            version (int, optional): Версия кэша.
        
        Returns:
            int: Новое значение.
        """
        # Уменьшаем значение в первом кэше
        value = self.caches[0].decr(key, delta, version)
        
        # Обновляем значение в остальных кэшах
        for cache in self.caches[1:]:
            cache.set(key, value, self.default_timeout, version)
        
        return value
    
    def has_key(self, key: str, version: Optional[int] = None) -> bool:
        """
        Проверяет, существует ли ключ в кэше.
        
        Args:
            key (str): Ключ.
            version (int, optional): Версия кэша.
        
        Returns:
            bool: True, если ключ существует, иначе False.
        """
        # Проверяем, существует ли ключ в любом из кэшей
        for cache in self.caches:
            if cache.has_key(key, version):
                return True
        
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Удаляет ключи, соответствующие шаблону.
        
        Args:
            pattern (str): Шаблон ключей.
        
        Returns:
            int: Количество удаленных ключей.
        """
        # Удаляем ключи из всех кэшей
        count = 0
        
        for cache in self.caches:
            if hasattr(cache, 'delete_pattern'):
                count += cache.delete_pattern(pattern)
        
        return count 
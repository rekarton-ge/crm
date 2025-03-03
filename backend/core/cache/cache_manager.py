"""
Менеджер кеша.

Этот модуль содержит класс для управления кешированием объектов.
"""

from typing import Optional, Any, Dict
from django.core.cache import cache
from django.db.models import Model

class CacheManager:
    """
    Менеджер кеша для работы с кешированными объектами.
    """
    
    def __init__(self, timeout: int = 3600):
        """
        Инициализирует менеджер кеша.
        
        Args:
            timeout: Время жизни кеша в секундах (по умолчанию 1 час)
        """
        self.timeout = timeout
    
    def _get_key(self, prefix: str, obj_id: int) -> str:
        """
        Формирует ключ кеша для объекта.
        
        Args:
            prefix: Префикс ключа
            obj_id: ID объекта
            
        Returns:
            str: Ключ кеша
        """
        return f"{prefix}:{obj_id}"
    
    def get_tag(self, tag_id: int) -> Optional[Model]:
        """
        Получает тег из кеша.
        
        Args:
            tag_id: ID тега
            
        Returns:
            Optional[Model]: Тег или None, если не найден в кеше
        """
        return cache.get(self._get_key("tag", tag_id))
    
    def set_tag(self, tag: Model) -> None:
        """
        Сохраняет тег в кеш.
        
        Args:
            tag: Тег для сохранения
        """
        cache.set(self._get_key("tag", tag.id), tag, self.timeout)
    
    def delete_tag(self, tag_id: int) -> None:
        """
        Удаляет тег из кеша.
        
        Args:
            tag_id: ID тега
        """
        cache.delete(self._get_key("tag", tag_id))
    
    def get_category(self, category_id: int) -> Optional[Model]:
        """
        Получает категорию из кеша.
        
        Args:
            category_id: ID категории
            
        Returns:
            Optional[Model]: Категория или None, если не найдена в кеше
        """
        return cache.get(self._get_key("category", category_id))
    
    def set_category(self, category: Model) -> None:
        """
        Сохраняет категорию в кеш.
        
        Args:
            category: Категория для сохранения
        """
        cache.set(self._get_key("category", category.id), category, self.timeout)
    
    def delete_category(self, category_id: int) -> None:
        """
        Удаляет категорию из кеша.
        
        Args:
            category_id: ID категории
        """
        cache.delete(self._get_key("category", category_id))
    
    def get_setting(self, setting_id: int) -> Optional[Model]:
        """
        Получает настройку из кеша.
        
        Args:
            setting_id: ID настройки
            
        Returns:
            Optional[Model]: Настройка или None, если не найдена в кеше
        """
        return cache.get(self._get_key("setting", setting_id))
    
    def set_setting(self, setting: Model) -> None:
        """
        Сохраняет настройку в кеш.
        
        Args:
            setting: Настройка для сохранения
        """
        cache.set(self._get_key("setting", setting.id), setting, self.timeout)
    
    def delete_setting(self, setting_id: int) -> None:
        """
        Удаляет настройку из кеша.
        
        Args:
            setting_id: ID настройки
        """
        cache.delete(self._get_key("setting", setting_id))
    
    def get_by_key(self, key: str) -> Optional[Any]:
        """
        Получает значение из кеша по ключу.
        
        Args:
            key: Ключ
            
        Returns:
            Optional[Any]: Значение или None, если не найдено в кеше
        """
        return cache.get(key)
    
    def set_by_key(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """
        Сохраняет значение в кеш по ключу.
        
        Args:
            key: Ключ
            value: Значение
            timeout: Время жизни кеша в секундах (если None, используется значение по умолчанию)
        """
        cache.set(key, value, timeout or self.timeout)
    
    def delete_by_key(self, key: str) -> None:
        """
        Удаляет значение из кеша по ключу.
        
        Args:
            key: Ключ
        """
        cache.delete(key)
    
    def clear(self) -> None:
        """
        Очищает весь кеш.
        """
        cache.clear()
    
    def get_many(self, keys: list) -> Dict[str, Any]:
        """
        Получает несколько значений из кеша по ключам.
        
        Args:
            keys: Список ключей
            
        Returns:
            Dict[str, Any]: Словарь с найденными значениями
        """
        return cache.get_many(keys)
    
    def set_many(self, data: Dict[str, Any], timeout: Optional[int] = None) -> None:
        """
        Сохраняет несколько значений в кеш.
        
        Args:
            data: Словарь с данными для сохранения
            timeout: Время жизни кеша в секундах (если None, используется значение по умолчанию)
        """
        cache.set_many(data, timeout or self.timeout)
    
    def delete_many(self, keys: list) -> None:
        """
        Удаляет несколько значений из кеша по ключам.
        
        Args:
            keys: Список ключей
        """
        cache.delete_many(keys)
    
    def incr(self, key: str, delta: int = 1) -> int:
        """
        Увеличивает значение в кеше.
        
        Args:
            key: Ключ
            delta: Значение для увеличения
            
        Returns:
            int: Новое значение
        """
        return cache.incr(key, delta)
    
    def decr(self, key: str, delta: int = 1) -> int:
        """
        Уменьшает значение в кеше.
        
        Args:
            key: Ключ
            delta: Значение для уменьшения
            
        Returns:
            int: Новое значение
        """
        return cache.decr(key, delta) 
"""
Модуль для индексации данных в CRM системе.

Этот модуль предоставляет классы для индексации различных типов данных,
включая модели Django, файлы и произвольный контент.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Type

from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseIndexer(ABC):
    """
    Базовый класс для всех индексаторов.
    
    Определяет общий интерфейс для индексации данных.
    """
    
    def __init__(self, index_name: str, settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует индексатор.
        
        Args:
            index_name: Имя индекса
            settings: Настройки индексатора
        """
        self.index_name = index_name
        self.settings = settings or {}
        self._initialize()
    
    def _initialize(self) -> None:
        """
        Инициализирует индексатор.
        """
        logger.debug(f"Initializing indexer for {self.index_name}")
    
    @abstractmethod
    def index(self, data: Any) -> bool:
        """
        Индексирует данные.
        
        Args:
            data: Данные для индексации
            
        Returns:
            bool: Успешность индексации
        """
        pass
    
    @abstractmethod
    def remove(self, identifier: str) -> bool:
        """
        Удаляет данные из индекса.
        
        Args:
            identifier: Идентификатор данных
            
        Returns:
            bool: Успешность удаления
        """
        pass
    
    @abstractmethod
    def update(self, identifier: str, data: Any) -> bool:
        """
        Обновляет данные в индексе.
        
        Args:
            identifier: Идентификатор данных
            data: Новые данные
            
        Returns:
            bool: Успешность обновления
        """
        pass
    
    def bulk_index(self, items: List[Any]) -> Dict[str, int]:
        """
        Индексирует несколько элементов.
        
        Args:
            items: Список элементов для индексации
            
        Returns:
            Dict[str, int]: Статистика индексации
        """
        success = 0
        failed = 0
        
        for item in items:
            try:
                if self.index(item):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error indexing item: {e}")
                failed += 1
        
        return {
            "total": len(items),
            "success": success,
            "failed": failed
        }


class ModelIndexer(BaseIndexer):
    """
    Индексатор для моделей Django.
    """
    
    def __init__(self, model: Type[models.Model], index_name: Optional[str] = None, 
                 fields: Optional[List[str]] = None, settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует индексатор для модели Django.
        
        Args:
            model: Класс модели Django
            index_name: Имя индекса (по умолчанию - имя модели)
            fields: Список полей для индексации (по умолчанию - все поля)
            settings: Настройки индексатора
        """
        self.model = model
        self.fields = fields
        index_name = index_name or model._meta.model_name
        super().__init__(index_name, settings)
    
    def _initialize(self) -> None:
        """
        Инициализирует индексатор для модели.
        """
        super()._initialize()
        
        if not self.fields:
            self.fields = [field.name for field in self.model._meta.fields 
                          if not field.name.startswith('_')]
        
        logger.debug(f"Model indexer initialized for {self.model.__name__} with fields: {self.fields}")
    
    def _prepare_document(self, instance: models.Model) -> Dict[str, Any]:
        """
        Подготавливает документ для индексации.
        
        Args:
            instance: Экземпляр модели
            
        Returns:
            Dict[str, Any]: Документ для индексации
        """
        document = {}
        
        for field in self.fields:
            if hasattr(instance, field):
                value = getattr(instance, field)
                if callable(value):
                    value = value()
                document[field] = value
        
        return document
    
    def index(self, instance: models.Model) -> bool:
        """
        Индексирует экземпляр модели.
        
        Args:
            instance: Экземпляр модели
            
        Returns:
            bool: Успешность индексации
        """
        if not isinstance(instance, self.model):
            logger.error(f"Instance {instance} is not of type {self.model.__name__}")
            return False
        
        try:
            document = self._prepare_document(instance)
            logger.debug(f"Indexing {self.model.__name__} with ID {instance.pk}")
            # Здесь должен быть код для фактической индексации
            return True
        except Exception as e:
            logger.error(f"Error indexing {self.model.__name__} with ID {instance.pk}: {e}")
            return False
    
    def remove(self, identifier: Union[str, int]) -> bool:
        """
        Удаляет экземпляр модели из индекса.
        
        Args:
            identifier: ID экземпляра модели
            
        Returns:
            bool: Успешность удаления
        """
        try:
            logger.debug(f"Removing {self.model.__name__} with ID {identifier} from index")
            # Здесь должен быть код для фактического удаления
            return True
        except Exception as e:
            logger.error(f"Error removing {self.model.__name__} with ID {identifier}: {e}")
            return False
    
    def update(self, identifier: Union[str, int], data: Optional[models.Model] = None) -> bool:
        """
        Обновляет экземпляр модели в индексе.
        
        Args:
            identifier: ID экземпляра модели
            data: Новый экземпляр модели (если None, будет загружен из БД)
            
        Returns:
            bool: Успешность обновления
        """
        try:
            if data is None:
                try:
                    data = self.model.objects.get(pk=identifier)
                except self.model.DoesNotExist:
                    logger.error(f"{self.model.__name__} with ID {identifier} does not exist")
                    return False
            
            return self.index(data)
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} with ID {identifier}: {e}")
            return False


class FileIndexer(BaseIndexer):
    """
    Индексатор для файлов.
    """
    
    def __init__(self, index_name: str, file_types: Optional[List[str]] = None, 
                 settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует индексатор для файлов.
        
        Args:
            index_name: Имя индекса
            file_types: Список типов файлов для индексации
            settings: Настройки индексатора
        """
        self.file_types = file_types or ['pdf', 'doc', 'docx', 'txt']
        super().__init__(index_name, settings)
    
    def index(self, file_path: str) -> bool:
        """
        Индексирует файл.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            bool: Успешность индексации
        """
        try:
            # Здесь должен быть код для извлечения текста из файла и его индексации
            logger.debug(f"Indexing file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return False
    
    def remove(self, identifier: str) -> bool:
        """
        Удаляет файл из индекса.
        
        Args:
            identifier: Идентификатор файла
            
        Returns:
            bool: Успешность удаления
        """
        try:
            logger.debug(f"Removing file with ID {identifier} from index")
            # Здесь должен быть код для фактического удаления
            return True
        except Exception as e:
            logger.error(f"Error removing file with ID {identifier}: {e}")
            return False
    
    def update(self, identifier: str, data: str) -> bool:
        """
        Обновляет файл в индексе.
        
        Args:
            identifier: Идентификатор файла
            data: Путь к новому файлу
            
        Returns:
            bool: Успешность обновления
        """
        try:
            self.remove(identifier)
            return self.index(data)
        except Exception as e:
            logger.error(f"Error updating file with ID {identifier}: {e}")
            return False


class ContentIndexer(BaseIndexer):
    """
    Индексатор для произвольного контента.
    """
    
    def index(self, data: Dict[str, Any]) -> bool:
        """
        Индексирует произвольный контент.
        
        Args:
            data: Данные для индексации
            
        Returns:
            bool: Успешность индексации
        """
        try:
            if 'id' not in data:
                logger.error("Content must have an 'id' field")
                return False
            
            logger.debug(f"Indexing content with ID {data['id']}")
            # Здесь должен быть код для фактической индексации
            return True
        except Exception as e:
            logger.error(f"Error indexing content: {e}")
            return False
    
    def remove(self, identifier: str) -> bool:
        """
        Удаляет контент из индекса.
        
        Args:
            identifier: Идентификатор контента
            
        Returns:
            bool: Успешность удаления
        """
        try:
            logger.debug(f"Removing content with ID {identifier} from index")
            # Здесь должен быть код для фактического удаления
            return True
        except Exception as e:
            logger.error(f"Error removing content with ID {identifier}: {e}")
            return False
    
    def update(self, identifier: str, data: Dict[str, Any]) -> bool:
        """
        Обновляет контент в индексе.
        
        Args:
            identifier: Идентификатор контента
            data: Новые данные
            
        Returns:
            bool: Успешность обновления
        """
        try:
            if 'id' not in data:
                data['id'] = identifier
            
            return self.index(data)
        except Exception as e:
            logger.error(f"Error updating content with ID {identifier}: {e}")
            return False

"""
Сервисы для работы с метаданными в CRM системе.

Этот модуль предоставляет сервисы для работы с метаданными,
включая индексацию и поиск.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Type, Tuple

from django.db import models
from django.conf import settings

from core.metadata.indexers import BaseIndexer, ModelIndexer, FileIndexer, ContentIndexer
from core.metadata.search import SearchEngine, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class MetadataService:
    """
    Базовый сервис для работы с метаданными.
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует сервис.
        
        Args:
            settings: Настройки сервиса
        """
        self.settings = settings or {}
        self._initialize()
    
    def _initialize(self) -> None:
        """
        Инициализирует сервис.
        """
        logger.debug("Initializing metadata service")


class IndexingService(MetadataService):
    """
    Сервис для индексации данных.
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует сервис индексации.
        
        Args:
            settings: Настройки сервиса
        """
        super().__init__(settings)
        self.indexers: Dict[str, BaseIndexer] = {}
    
    def _initialize(self) -> None:
        """
        Инициализирует сервис индексации.
        """
        super()._initialize()
        logger.debug("Initializing indexing service")
    
    def register_indexer(self, name: str, indexer: BaseIndexer) -> None:
        """
        Регистрирует индексатор.
        
        Args:
            name: Имя индексатора
            indexer: Индексатор
        """
        logger.debug(f"Registering indexer: {name}")
        self.indexers[name] = indexer
    
    def get_indexer(self, name: str) -> Optional[BaseIndexer]:
        """
        Получает индексатор по имени.
        
        Args:
            name: Имя индексатора
            
        Returns:
            Optional[BaseIndexer]: Индексатор или None, если индексатор не найден
        """
        return self.indexers.get(name)
    
    def create_model_indexer(self, model: Type[models.Model], name: Optional[str] = None, 
                            fields: Optional[List[str]] = None) -> ModelIndexer:
        """
        Создает индексатор для модели Django.
        
        Args:
            model: Класс модели Django
            name: Имя индексатора (по умолчанию - имя модели)
            fields: Список полей для индексации
            
        Returns:
            ModelIndexer: Созданный индексатор
        """
        name = name or model._meta.model_name
        indexer = ModelIndexer(model, name, fields, self.settings.get('model_indexer', {}))
        self.register_indexer(name, indexer)
        return indexer
    
    def create_file_indexer(self, name: str, file_types: Optional[List[str]] = None) -> FileIndexer:
        """
        Создает индексатор для файлов.
        
        Args:
            name: Имя индексатора
            file_types: Список типов файлов для индексации
            
        Returns:
            FileIndexer: Созданный индексатор
        """
        indexer = FileIndexer(name, file_types, self.settings.get('file_indexer', {}))
        self.register_indexer(name, indexer)
        return indexer
    
    def create_content_indexer(self, name: str) -> ContentIndexer:
        """
        Создает индексатор для произвольного контента.
        
        Args:
            name: Имя индексатора
            
        Returns:
            ContentIndexer: Созданный индексатор
        """
        indexer = ContentIndexer(name, self.settings.get('content_indexer', {}))
        self.register_indexer(name, indexer)
        return indexer
    
    def index_model(self, model: Type[models.Model], instance: models.Model, 
                   indexer_name: Optional[str] = None) -> bool:
        """
        Индексирует экземпляр модели.
        
        Args:
            model: Класс модели Django
            instance: Экземпляр модели
            indexer_name: Имя индексатора (по умолчанию - имя модели)
            
        Returns:
            bool: Успешность индексации
        """
        indexer_name = indexer_name or model._meta.model_name
        indexer = self.get_indexer(indexer_name)
        
        if not indexer:
            logger.error(f"Indexer {indexer_name} not found")
            return False
        
        if not isinstance(indexer, ModelIndexer):
            logger.error(f"Indexer {indexer_name} is not a ModelIndexer")
            return False
        
        return indexer.index(instance)
    
    def index_file(self, file_path: str, indexer_name: str) -> bool:
        """
        Индексирует файл.
        
        Args:
            file_path: Путь к файлу
            indexer_name: Имя индексатора
            
        Returns:
            bool: Успешность индексации
        """
        indexer = self.get_indexer(indexer_name)
        
        if not indexer:
            logger.error(f"Indexer {indexer_name} not found")
            return False
        
        if not isinstance(indexer, FileIndexer):
            logger.error(f"Indexer {indexer_name} is not a FileIndexer")
            return False
        
        return indexer.index(file_path)
    
    def index_content(self, content: Dict[str, Any], indexer_name: str) -> bool:
        """
        Индексирует произвольный контент.
        
        Args:
            content: Контент для индексации
            indexer_name: Имя индексатора
            
        Returns:
            bool: Успешность индексации
        """
        indexer = self.get_indexer(indexer_name)
        
        if not indexer:
            logger.error(f"Indexer {indexer_name} not found")
            return False
        
        if not isinstance(indexer, ContentIndexer):
            logger.error(f"Indexer {indexer_name} is not a ContentIndexer")
            return False
        
        return indexer.index(content)


class SearchService(MetadataService):
    """
    Сервис для поиска по метаданным.
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Инициализирует сервис поиска.
        
        Args:
            settings: Настройки сервиса
        """
        super().__init__(settings)
        self.engines: Dict[str, SearchEngine] = {}
    
    def _initialize(self) -> None:
        """
        Инициализирует сервис поиска.
        """
        super()._initialize()
        logger.debug("Initializing search service")
    
    def register_engine(self, name: str, engine: SearchEngine) -> None:
        """
        Регистрирует движок поиска.
        
        Args:
            name: Имя движка
            engine: Движок поиска
        """
        logger.debug(f"Registering search engine: {name}")
        self.engines[name] = engine
    
    def get_engine(self, name: str) -> Optional[SearchEngine]:
        """
        Получает движок поиска по имени.
        
        Args:
            name: Имя движка
            
        Returns:
            Optional[SearchEngine]: Движок поиска или None, если движок не найден
        """
        return self.engines.get(name)
    
    def create_engine(self, name: str, index_name: Optional[str] = None) -> SearchEngine:
        """
        Создает движок поиска.
        
        Args:
            name: Имя движка
            index_name: Имя индекса
            
        Returns:
            SearchEngine: Созданный движок поиска
        """
        engine = SearchEngine(index_name, self.settings.get('search_engine', {}))
        self.register_engine(name, engine)
        return engine
    
    def search(self, query: Union[str, SearchQuery], engine_name: str, 
              index_name: Optional[str] = None) -> Tuple[List[SearchResult], int]:
        """
        Выполняет поиск.
        
        Args:
            query: Строка запроса или объект SearchQuery
            engine_name: Имя движка поиска
            index_name: Имя индекса
            
        Returns:
            Tuple[List[SearchResult], int]: Список результатов и общее количество найденных документов
        """
        engine = self.get_engine(engine_name)
        
        if not engine:
            logger.error(f"Search engine {engine_name} not found")
            return [], 0
        
        return engine.search(query, index_name)
    
    def get_by_id(self, id: str, engine_name: str, index_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Получает документ по ID.
        
        Args:
            id: ID документа
            engine_name: Имя движка поиска
            index_name: Имя индекса
            
        Returns:
            Optional[Dict[str, Any]]: Документ или None, если документ не найден
        """
        engine = self.get_engine(engine_name)
        
        if not engine:
            logger.error(f"Search engine {engine_name} not found")
            return None
        
        return engine.get_by_id(id, index_name)
    
    def count(self, query: Union[str, SearchQuery], engine_name: str, 
             index_name: Optional[str] = None) -> int:
        """
        Подсчитывает количество документов, соответствующих запросу.
        
        Args:
            query: Строка запроса или объект SearchQuery
            engine_name: Имя движка поиска
            index_name: Имя индекса
            
        Returns:
            int: Количество документов
        """
        engine = self.get_engine(engine_name)
        
        if not engine:
            logger.error(f"Search engine {engine_name} not found")
            return 0
        
        return engine.count(query, index_name)

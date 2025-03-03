"""
Модуль для работы с метаданными в CRM системе.

Этот модуль предоставляет функциональность для индексации, поиска и 
управления метаданными различных объектов в системе.
"""

from core.metadata.indexers import (
    BaseIndexer, ModelIndexer, FileIndexer, ContentIndexer
)
from core.metadata.search import (
    SearchEngine, SearchQuery, SearchResult, SearchFilter
)
from core.metadata.services import (
    MetadataService, IndexingService, SearchService
)

__all__ = [
    # Индексаторы
    'BaseIndexer',
    'ModelIndexer',
    'FileIndexer',
    'ContentIndexer',
    
    # Поиск
    'SearchEngine',
    'SearchQuery',
    'SearchResult',
    'SearchFilter',
    
    # Сервисы
    'MetadataService',
    'IndexingService',
    'SearchService',
]

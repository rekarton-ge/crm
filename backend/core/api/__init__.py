"""
Пакет API для модуля Core.

Предоставляет компоненты API для модуля Core, включая сериализаторы,
представления, разрешения, фильтры и документацию.
"""

# Версия API
__version__ = '0.1.0'

# Экспорт основных компонентов для удобства импорта
from core.api.serializers import (
    BaseSerializer, BaseModelSerializer, ContentTypeField, GenericRelatedField,
    DynamicFieldsModelSerializer, ErrorSerializer, PaginatedResponseSerializer
)

from core.api.permissions import (
    IsAdminUser, IsAuthenticated, ReadOnly, IsOwner, ReadOnlyOrAdmin, ActionBasedPermission
)

from core.api.filters import (
    CoreFilterSet, create_boolean_filter, create_date_range_filter,
    create_choice_filter, create_text_filter, create_number_range_filter
)

from core.api.pagination import (
    StandardResultsSetPagination, LargeResultsSetPagination,
    SmallResultsSetPagination, CustomPagination
)

from core.api.exception_handlers import custom_exception_handler

# Представления для основных компонентов
from core.api.views import SettingViewSet, TagViewSet, TaggedItemViewSet

__all__ = [
    # Базовые компоненты
    'BaseSerializer',
    'BaseModelSerializer',
    'ContentTypeField',
    'GenericRelatedField',
    'DynamicFieldsModelSerializer',
    'ErrorSerializer',
    'PaginatedResponseSerializer',

    # Разрешения
    'IsAdminUser',
    'IsAuthenticated',
    'ReadOnly',
    'IsOwner',
    'ReadOnlyOrAdmin',
    'ActionBasedPermission',

    # Фильтры
    'CoreFilterSet',
    'create_boolean_filter',
    'create_date_range_filter',
    'create_choice_filter',
    'create_text_filter',
    'create_number_range_filter',

    # Пагинация
    'StandardResultsSetPagination',
    'LargeResultsSetPagination',
    'SmallResultsSetPagination',
    'CustomPagination',

    # Обработчики исключений
    'custom_exception_handler',

    # Представления
    'SettingViewSet',
    'TagViewSet',
    'TaggedItemViewSet',

    # Версия
    '__version__',
]
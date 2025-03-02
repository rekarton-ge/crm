"""
Пакет сериализаторов API Core.

Этот пакет содержит все сериализаторы для работы с API модуля Core,
включая базовые сериализаторы, сериализаторы настроек и тегов.
"""

from core.api.serializers.base import (
    BaseSerializer,
    BaseModelSerializer,
    BaseReadOnlyModelSerializer,
    ContentTypeField,
    GenericRelatedField,
    DynamicFieldsModelSerializer,
    ErrorSerializer,
    PaginatedResponseSerializer
)

from core.api.serializers.settings import (
    SettingSerializer,
    SettingCreateSerializer,
    SettingUpdateSerializer,
    SettingBulkUpdateSerializer,
    SettingCategorySerializer,
    SettingListByCategorySerializer
)

from core.api.serializers.tags import (
    TagSerializer,
    TagCreateSerializer,
    TagUpdateSerializer,
    GenericTaggedItemSerializer,
    TaggedItemCreateSerializer,
    TaggedItemDeleteSerializer,
    TagWithObjectCountSerializer,
    ObjectTagsSerializer,
    BulkTagsSerializer
)

__all__ = [
    # Базовые сериализаторы
    'BaseSerializer',
    'BaseModelSerializer',
    'BaseReadOnlyModelSerializer',
    'ContentTypeField',
    'GenericRelatedField',
    'DynamicFieldsModelSerializer',
    'ErrorSerializer',
    'PaginatedResponseSerializer',

    # Сериализаторы настроек
    'SettingSerializer',
    'SettingCreateSerializer',
    'SettingUpdateSerializer',
    'SettingBulkUpdateSerializer',
    'SettingCategorySerializer',
    'SettingListByCategorySerializer',

    # Сериализаторы тегов
    'TagSerializer',
    'TagCreateSerializer',
    'TagUpdateSerializer',
    'GenericTaggedItemSerializer',
    'TaggedItemCreateSerializer',
    'TaggedItemDeleteSerializer',
    'TagWithObjectCountSerializer',
    'ObjectTagsSerializer',
    'BulkTagsSerializer'
]
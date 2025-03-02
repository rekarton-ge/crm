"""
Пакет для работы с кэшированием.

Этот пакет содержит утилиты и декораторы для эффективного кэширования данных
и ответов API, с целью повышения производительности и снижения нагрузки на базу данных.
"""

from core.cache.cache_utils import (
    generate_cache_key,
    cache_get_or_set,
    invalidate_cache_keys,
    invalidate_cache_prefix,
    get_model_cache_key,
    invalidate_model_cache,
    get_queryset_cache_key,
    cache_queryset,
    is_cache_enabled,
    CacheManager
)

from core.cache.decorators import (
    cache_result,
    cache_method_result,
    cache_property,
    cache_response,
    invalidate_cache_on_save,
    disable_cache_for_user
)

__all__ = [
    # Утилиты кэширования
    'generate_cache_key',
    'cache_get_or_set',
    'invalidate_cache_keys',
    'invalidate_cache_prefix',
    'get_model_cache_key',
    'invalidate_model_cache',
    'get_queryset_cache_key',
    'cache_queryset',
    'is_cache_enabled',
    'CacheManager',

    # Декораторы кэширования
    'cache_result',
    'cache_method_result',
    'cache_property',
    'cache_response',
    'invalidate_cache_on_save',
    'disable_cache_for_user'
]
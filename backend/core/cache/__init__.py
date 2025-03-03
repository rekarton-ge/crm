"""
Модуль кэширования.

Этот модуль содержит функции и классы для работы с кэшем.
"""

from core.cache.cache_utils import (
    get_cache_key,
    cache_result,
    invalidate_cache,
    invalidate_cache_pattern,
    cache_queryset,
    cache_model_instance,
    cache_function,
    CacheManager,
)

from core.cache.decorators import (
    cache_result as cache_result_decorator,
    cache_method_result,
    cache_property,
    cache_response,
    invalidate_cache_on_save,
    disable_cache_for_user,
    override_cache_settings,
)

from core.cache.middleware import (
    CacheMiddleware,
    CacheControlMiddleware,
    ConditionalGetMiddleware,
)

from core.cache.settings import (
    get_cache_settings,
    get_cache_middleware_settings,
    get_cache_control_settings,
    is_cache_enabled,
    get_cache_timeout,
    get_cache_key_prefix,
    get_cache_version,
)

from core.cache.backends import (
    PrefixedCache,
    PatternRedisCache,
    PatternLocMemCache,
    TieredCache,
)


__all__ = [
    # cache_utils.py
    'get_cache_key',
    'cache_result',
    'invalidate_cache',
    'invalidate_cache_pattern',
    'cache_queryset',
    'cache_model_instance',
    'cache_function',
    'CacheManager',
    
    # decorators.py
    'cache_result_decorator',
    'cache_method_result',
    'cache_property',
    'cache_response',
    'invalidate_cache_on_save',
    'disable_cache_for_user',
    'override_cache_settings',
    
    # middleware.py
    'CacheMiddleware',
    'CacheControlMiddleware',
    'ConditionalGetMiddleware',
    
    # settings.py
    'get_cache_settings',
    'get_cache_middleware_settings',
    'get_cache_control_settings',
    'is_cache_enabled',
    'get_cache_timeout',
    'get_cache_key_prefix',
    'get_cache_version',
    
    # backends.py
    'PrefixedCache',
    'PatternRedisCache',
    'PatternLocMemCache',
    'TieredCache',
]
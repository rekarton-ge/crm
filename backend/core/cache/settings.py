"""
Настройки кэширования.

Этот модуль содержит настройки и конфигурацию для кэширования.
"""

from typing import Any, Dict, List, Optional, Union

from django.conf import settings


# Настройки кэширования по умолчанию
DEFAULT_CACHE_TIMEOUT = 3600  # 1 час
DEFAULT_CACHE_KEY_PREFIX = 'crm'
DEFAULT_CACHE_VERSION = 1


def get_cache_settings() -> Dict[str, Any]:
    """
    Возвращает настройки кэширования.
    
    Returns:
        Dict[str, Any]: Настройки кэширования.
    """
    return {
        'default': {
            'BACKEND': getattr(
                settings,
                'CACHE_BACKEND',
                'django.core.cache.backends.locmem.LocMemCache'
            ),
            'LOCATION': getattr(
                settings,
                'CACHE_LOCATION',
                'unique-snowflake'
            ),
            'TIMEOUT': getattr(
                settings,
                'CACHE_TIMEOUT',
                DEFAULT_CACHE_TIMEOUT
            ),
            'OPTIONS': getattr(
                settings,
                'CACHE_OPTIONS',
                {}
            ),
            'KEY_PREFIX': getattr(
                settings,
                'CACHE_KEY_PREFIX',
                DEFAULT_CACHE_KEY_PREFIX
            ),
            'VERSION': getattr(
                settings,
                'CACHE_VERSION',
                DEFAULT_CACHE_VERSION
            ),
        }
    }


def get_cache_middleware_settings() -> Dict[str, Any]:
    """
    Возвращает настройки middleware для кэширования.
    
    Returns:
        Dict[str, Any]: Настройки middleware для кэширования.
    """
    return {
        'CACHE_MIDDLEWARE_SECONDS': getattr(
            settings,
            'CACHE_MIDDLEWARE_SECONDS',
            DEFAULT_CACHE_TIMEOUT
        ),
        'CACHE_MIDDLEWARE_KEY_PREFIX': getattr(
            settings,
            'CACHE_MIDDLEWARE_KEY_PREFIX',
            DEFAULT_CACHE_KEY_PREFIX
        ),
        'CACHE_MIDDLEWARE_ANONYMOUS_ONLY': getattr(
            settings,
            'CACHE_MIDDLEWARE_ANONYMOUS_ONLY',
            False
        ),
        'CACHE_MIDDLEWARE_EXCLUDE_PATHS': getattr(
            settings,
            'CACHE_MIDDLEWARE_EXCLUDE_PATHS',
            [
                r'^/admin/',
                r'^/api/auth/',
                r'^/api/users/me/',
            ]
        ),
        'CACHE_MIDDLEWARE_INCLUDE_PATHS': getattr(
            settings,
            'CACHE_MIDDLEWARE_INCLUDE_PATHS',
            []
        ),
        'CACHE_MIDDLEWARE_STATUS_CODES': getattr(
            settings,
            'CACHE_MIDDLEWARE_STATUS_CODES',
            [200]
        ),
    }


def get_cache_control_settings() -> Dict[str, Any]:
    """
    Возвращает настройки Cache-Control.
    
    Returns:
        Dict[str, Any]: Настройки Cache-Control.
    """
    return {
        'default': {
            'public': True,
            'max_age': DEFAULT_CACHE_TIMEOUT,
        },
        'paths': {
            r'^/static/': {
                'public': True,
                'max_age': 86400,  # 1 день
            },
            r'^/media/': {
                'public': True,
                'max_age': 86400,  # 1 день
            },
            r'^/api/auth/': {
                'private': True,
                'no_cache': True,
                'no_store': True,
                'max_age': 0,
            },
        }
    }


def is_cache_enabled() -> bool:
    """
    Проверяет, включен ли кэш.
    
    Returns:
        bool: True, если кэш включен, иначе False.
    """
    return getattr(settings, 'USE_CACHE', True)


def get_cache_timeout(timeout: Optional[int] = None) -> int:
    """
    Возвращает время жизни кэша.
    
    Args:
        timeout (int, optional): Время жизни кэша в секундах.
            По умолчанию используется значение из настроек Django.
    
    Returns:
        int: Время жизни кэша в секундах.
    """
    if timeout is not None:
        return timeout
    
    return getattr(settings, 'CACHE_TIMEOUT', DEFAULT_CACHE_TIMEOUT)


def get_cache_key_prefix() -> str:
    """
    Возвращает префикс ключа кэша.
    
    Returns:
        str: Префикс ключа кэша.
    """
    return getattr(settings, 'CACHE_KEY_PREFIX', DEFAULT_CACHE_KEY_PREFIX)


def get_cache_version() -> int:
    """
    Возвращает версию кэша.
    
    Returns:
        int: Версия кэша.
    """
    return getattr(settings, 'CACHE_VERSION', DEFAULT_CACHE_VERSION) 
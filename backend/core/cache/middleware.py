"""
Middleware для кэширования.

Этот модуль содержит middleware для кэширования ответов HTTP запросов.
"""

import hashlib
import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional, Pattern, Union

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_bytes

logger = logging.getLogger(__name__)


class CacheMiddleware(MiddlewareMixin):
    """
    Middleware для кэширования ответов HTTP запросов.
    
    Кэширует ответы для GET и HEAD запросов, если они соответствуют условиям.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.cache_timeout = getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 3600)
        self.key_prefix = getattr(settings, 'CACHE_MIDDLEWARE_KEY_PREFIX', 'middleware')
        self.cache_anonymous_only = getattr(settings, 'CACHE_MIDDLEWARE_ANONYMOUS_ONLY', False)
        
        # Пути, которые не нужно кэшировать
        self.cache_exclude_paths = getattr(settings, 'CACHE_MIDDLEWARE_EXCLUDE_PATHS', [])
        self.cache_exclude_paths_compiled = [re.compile(path) for path in self.cache_exclude_paths]
        
        # Пути, которые нужно кэшировать
        self.cache_include_paths = getattr(settings, 'CACHE_MIDDLEWARE_INCLUDE_PATHS', [])
        self.cache_include_paths_compiled = [re.compile(path) for path in self.cache_include_paths]
        
        # Статус-коды, которые нужно кэшировать
        self.cache_status_codes = getattr(settings, 'CACHE_MIDDLEWARE_STATUS_CODES', [200])
    
    def _should_cache_response(self, request: HttpRequest, response: HttpResponse) -> bool:
        """
        Проверяет, нужно ли кэшировать ответ.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            bool: True, если ответ нужно кэшировать, иначе False.
        """
        # Проверяем, включен ли кэш
        if not getattr(settings, 'USE_CACHE', True):
            return False
        
        # Проверяем метод запроса
        if request.method not in ('GET', 'HEAD'):
            return False
        
        # Проверяем статус-код ответа
        if response.status_code not in self.cache_status_codes:
            return False
        
        # Проверяем, аутентифицирован ли пользователь
        if self.cache_anonymous_only and request.user.is_authenticated:
            return False
        
        # Проверяем, есть ли заголовок Cache-Control: no-cache
        if 'no-cache' in response.get('Cache-Control', ''):
            return False
        
        # Проверяем, соответствует ли путь исключениям
        path = request.path
        for pattern in self.cache_exclude_paths_compiled:
            if pattern.match(path):
                return False
        
        # Проверяем, соответствует ли путь включениям
        if self.cache_include_paths_compiled:
            for pattern in self.cache_include_paths_compiled:
                if pattern.match(path):
                    return True
            return False
        
        return True
    
    def _get_cache_key(self, request: HttpRequest) -> str:
        """
        Генерирует ключ кэша для запроса.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            str: Ключ кэша.
        """
        # Получаем полный URL запроса
        url = request.get_full_path()
        
        # Получаем информацию о пользователе
        if request.user.is_authenticated:
            user_id = str(request.user.pk)
        else:
            user_id = 'anonymous'
        
        # Получаем информацию о языке
        lang = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'default'
        
        # Создаем строку для хеширования
        key_data = f"{self.key_prefix}:{url}:{user_id}:{lang}"
        
        # Создаем хеш
        key_hash = hashlib.md5(force_bytes(key_data)).hexdigest()
        
        return f"cache_middleware:{key_hash}"
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Обрабатывает запрос и возвращает ответ из кэша, если он есть.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            Optional[HttpResponse]: Ответ из кэша или None.
        """
        # Проверяем, включен ли кэш
        if not getattr(settings, 'USE_CACHE', True):
            return None
        
        # Проверяем метод запроса
        if request.method not in ('GET', 'HEAD'):
            return None
        
        # Проверяем, аутентифицирован ли пользователь
        if self.cache_anonymous_only and request.user.is_authenticated:
            return None
        
        # Получаем ключ кэша
        cache_key = self._get_cache_key(request)
        
        # Пытаемся получить ответ из кэша
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_response
        
        logger.debug(f"Cache miss for key: {cache_key}")
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Обрабатывает ответ и сохраняет его в кэш, если нужно.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            HttpResponse: HTTP ответ.
        """
        # Проверяем, нужно ли кэшировать ответ
        if not self._should_cache_response(request, response):
            return response
        
        # Получаем ключ кэша
        cache_key = self._get_cache_key(request)
        
        # Сохраняем ответ в кэш
        cache.set(cache_key, response, self.cache_timeout)
        logger.debug(f"Cached response for key: {cache_key}")
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware для управления заголовками Cache-Control.
    
    Добавляет заголовки Cache-Control к ответам в зависимости от настроек.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.cache_control_settings = getattr(settings, 'CACHE_CONTROL_SETTINGS', {})
        
        # Настройки по умолчанию
        self.default_settings = self.cache_control_settings.get('default', {
            'public': True,
            'max_age': 3600,
        })
        
        # Настройки для конкретных путей
        self.path_settings = self.cache_control_settings.get('paths', {})
        self.path_settings_compiled = {
            re.compile(path): settings for path, settings in self.path_settings.items()
        }
    
    def _get_cache_control_settings(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Получает настройки Cache-Control для запроса.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            Dict[str, Any]: Настройки Cache-Control.
        """
        path = request.path
        
        # Проверяем, соответствует ли путь настройкам
        for pattern, settings in self.path_settings_compiled.items():
            if pattern.match(path):
                return settings
        
        return self.default_settings
    
    def _build_cache_control_header(self, settings: Dict[str, Any]) -> str:
        """
        Создает заголовок Cache-Control на основе настроек.
        
        Args:
            settings (Dict[str, Any]): Настройки Cache-Control.
        
        Returns:
            str: Заголовок Cache-Control.
        """
        directives = []
        
        # Добавляем директивы
        if settings.get('public'):
            directives.append('public')
        elif settings.get('private'):
            directives.append('private')
        
        if settings.get('no_cache'):
            directives.append('no-cache')
        
        if settings.get('no_store'):
            directives.append('no-store')
        
        if settings.get('max_age') is not None:
            directives.append(f"max-age={settings['max_age']}")
        
        if settings.get('s_maxage') is not None:
            directives.append(f"s-maxage={settings['s_maxage']}")
        
        if settings.get('must_revalidate'):
            directives.append('must-revalidate')
        
        if settings.get('proxy_revalidate'):
            directives.append('proxy-revalidate')
        
        return ', '.join(directives)
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Обрабатывает ответ и добавляет заголовки Cache-Control.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            HttpResponse: HTTP ответ с заголовками Cache-Control.
        """
        # Проверяем, нужно ли добавлять заголовки
        if not getattr(settings, 'USE_CACHE_CONTROL', True):
            return response
        
        # Не добавляем заголовки, если они уже есть
        if 'Cache-Control' in response:
            return response
        
        # Получаем настройки Cache-Control
        settings = self._get_cache_control_settings(request)
        
        # Создаем заголовок Cache-Control
        cache_control = self._build_cache_control_header(settings)
        
        # Добавляем заголовок Cache-Control
        if cache_control:
            response['Cache-Control'] = cache_control
        
        return response


class ConditionalGetMiddleware(MiddlewareMixin):
    """
    Middleware для условных GET запросов.
    
    Обрабатывает заголовки If-Modified-Since и If-None-Match для условных GET запросов.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Обрабатывает ответ и проверяет условные заголовки.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            HttpResponse: HTTP ответ.
        """
        # Проверяем, включен ли условный GET
        if not getattr(settings, 'USE_CONDITIONAL_GET', True):
            return response
        
        # Проверяем метод запроса
        if request.method != 'GET':
            return response
        
        # Проверяем статус-код ответа
        if response.status_code != 200:
            return response
        
        # Проверяем заголовок ETag
        etag = response.get('ETag')
        if etag and request.META.get('HTTP_IF_NONE_MATCH') == etag:
            logger.debug(f"Conditional GET: ETag match for {request.path}")
            return HttpResponse(status=304)
        
        # Проверяем заголовок Last-Modified
        last_modified = response.get('Last-Modified')
        if last_modified and request.META.get('HTTP_IF_MODIFIED_SINCE') == last_modified:
            logger.debug(f"Conditional GET: Last-Modified match for {request.path}")
            return HttpResponse(status=304)
        
        return response 
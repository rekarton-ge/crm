"""
Middleware для измерения времени ответа.

Этот модуль содержит middleware для измерения времени ответа HTTP запросов.
"""

import time
from typing import Any, Callable, Dict, List, Optional, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class ResponseTimeMiddleware(MiddlewareMixin):
    """
    Middleware для измерения времени ответа HTTP запросов.
    
    Добавляет заголовок X-Response-Time с временем ответа в миллисекундах.
    """
    
    def __init__(self, get_response=None):
        """
        Инициализация middleware.
        
        Args:
            get_response: Функция для получения ответа.
        """
        super().__init__(get_response)
        self.enable_response_time = getattr(settings, 'ENABLE_RESPONSE_TIME', True)
        self.header_name = getattr(settings, 'RESPONSE_TIME_HEADER', 'X-Response-Time')
        self.exclude_paths = getattr(settings, 'RESPONSE_TIME_EXCLUDE_PATHS', [])
        self.exclude_extensions = getattr(settings, 'RESPONSE_TIME_EXCLUDE_EXTENSIONS', ['.css', '.js', '.ico', '.jpg', '.png', '.gif'])
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Обрабатывает запрос и добавляет время начала запроса.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            Optional[HttpResponse]: HTTP ответ или None.
        """
        if not self.enable_response_time:
            return None
        
        # Проверяем, нужно ли измерять время ответа
        if not self._should_measure_time(request):
            return None
        
        # Добавляем время начала запроса
        request.start_time = time.time()
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Обрабатывает ответ и добавляет заголовок с временем ответа.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            HttpResponse: HTTP ответ с добавленным заголовком.
        """
        if not self.enable_response_time:
            return response
        
        # Проверяем, нужно ли измерять время ответа
        if not self._should_measure_time(request):
            return response
        
        # Проверяем, есть ли время начала запроса
        if not hasattr(request, 'start_time'):
            return response
        
        # Вычисляем время выполнения запроса
        duration = time.time() - request.start_time
        
        # Добавляем заголовок с временем ответа
        response[self.header_name] = f"{round(duration * 1000, 2)}ms"
        
        return response
    
    def _should_measure_time(self, request: HttpRequest) -> bool:
        """
        Проверяет, нужно ли измерять время ответа для запроса.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            bool: True, если нужно измерять время ответа, иначе False.
        """
        # Проверяем путь запроса
        path = request.path
        
        # Проверяем, соответствует ли путь исключениям
        for exclude_path in self.exclude_paths:
            if exclude_path in path:
                return False
        
        # Проверяем расширение файла
        for extension in self.exclude_extensions:
            if path.endswith(extension):
                return False
        
        return True

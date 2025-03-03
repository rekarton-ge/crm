"""
Middleware для логирования запросов.

Этот модуль содержит middleware для логирования HTTP запросов.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger('request')


class RequestLogMiddleware(MiddlewareMixin):
    """
    Middleware для логирования HTTP запросов.
    
    Логирует информацию о запросах и ответах, включая метод, путь, статус, время выполнения.
    """
    
    def __init__(self, get_response=None):
        """
        Инициализация middleware.
        
        Args:
            get_response: Функция для получения ответа.
        """
        super().__init__(get_response)
        self.enable_request_log = getattr(settings, 'ENABLE_REQUEST_LOG', True)
        self.log_request_body = getattr(settings, 'LOG_REQUEST_BODY', False)
        self.log_response_body = getattr(settings, 'LOG_RESPONSE_BODY', False)
        self.max_body_length = getattr(settings, 'MAX_BODY_LOG_LENGTH', 1000)
        self.exclude_paths = getattr(settings, 'REQUEST_LOG_EXCLUDE_PATHS', [])
        self.exclude_extensions = getattr(settings, 'REQUEST_LOG_EXCLUDE_EXTENSIONS', ['.css', '.js', '.ico', '.jpg', '.png', '.gif'])
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Обрабатывает запрос и добавляет время начала запроса.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            Optional[HttpResponse]: HTTP ответ или None.
        """
        if not self.enable_request_log:
            return None
        
        # Проверяем, нужно ли логировать запрос
        if not self._should_log_request(request):
            return None
        
        # Добавляем время начала запроса
        request.start_time = time.time()
        
        # Логируем запрос
        self._log_request(request)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Обрабатывает ответ и логирует информацию о запросе и ответе.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
        
        Returns:
            HttpResponse: HTTP ответ.
        """
        if not self.enable_request_log:
            return response
        
        # Проверяем, нужно ли логировать запрос
        if not self._should_log_request(request):
            return response
        
        # Проверяем, есть ли время начала запроса
        if not hasattr(request, 'start_time'):
            return response
        
        # Вычисляем время выполнения запроса
        duration = time.time() - request.start_time
        
        # Логируем ответ
        self._log_response(request, response, duration)
        
        return response
    
    def _should_log_request(self, request: HttpRequest) -> bool:
        """
        Проверяет, нужно ли логировать запрос.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            bool: True, если запрос нужно логировать, иначе False.
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
    
    def _log_request(self, request: HttpRequest) -> None:
        """
        Логирует информацию о запросе.
        
        Args:
            request (HttpRequest): HTTP запрос.
        """
        # Получаем метод и путь запроса
        method = request.method
        path = request.get_full_path()
        
        # Получаем IP-адрес клиента
        ip = self._get_client_ip(request)
        
        # Получаем информацию о пользователе
        user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        
        # Формируем сообщение для лога
        log_data = {
            'method': method,
            'path': path,
            'ip': ip,
            'user': user,
        }
        
        # Добавляем тело запроса, если нужно
        if self.log_request_body and request.body:
            try:
                body = request.body.decode('utf-8')
                if len(body) > self.max_body_length:
                    body = body[:self.max_body_length] + '...'
                log_data['body'] = body
            except Exception as e:
                log_data['body_error'] = str(e)
        
        # Логируем запрос
        logger.info(f"Request: {json.dumps(log_data)}")
    
    def _log_response(self, request: HttpRequest, response: HttpResponse, duration: float) -> None:
        """
        Логирует информацию об ответе.
        
        Args:
            request (HttpRequest): HTTP запрос.
            response (HttpResponse): HTTP ответ.
            duration (float): Время выполнения запроса в секундах.
        """
        # Получаем метод и путь запроса
        method = request.method
        path = request.get_full_path()
        
        # Получаем статус ответа
        status_code = response.status_code
        
        # Формируем сообщение для лога
        log_data = {
            'method': method,
            'path': path,
            'status': status_code,
            'duration': round(duration * 1000, 2),  # в миллисекундах
        }
        
        # Добавляем тело ответа, если нужно
        if self.log_response_body and hasattr(response, 'content'):
            try:
                if isinstance(response, JsonResponse):
                    body = json.loads(response.content.decode('utf-8'))
                else:
                    body = response.content.decode('utf-8')
                
                if isinstance(body, str) and len(body) > self.max_body_length:
                    body = body[:self.max_body_length] + '...'
                
                log_data['body'] = body
            except Exception as e:
                log_data['body_error'] = str(e)
        
        # Логируем ответ
        log_level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(log_level, f"Response: {json.dumps(log_data)}")
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Получает IP-адрес клиента.
        
        Args:
            request (HttpRequest): HTTP запрос.
        
        Returns:
            str: IP-адрес клиента.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip

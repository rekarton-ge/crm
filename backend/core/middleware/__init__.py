"""
Middleware для приложения.

Этот пакет содержит middleware для приложения Django.
"""

from core.middleware.request_log import RequestLogMiddleware
from core.middleware.response_time import ResponseTimeMiddleware


__all__ = [
    'RequestLogMiddleware',
    'ResponseTimeMiddleware',
]

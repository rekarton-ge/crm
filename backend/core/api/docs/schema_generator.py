"""
Генератор схем API.

Этот модуль предоставляет инструменты для автоматической генерации схем API
на основе представлений Django REST Framework и их сериализаторов.
"""

import inspect
import re
import json
from typing import Dict, List, Any, Optional, Type, Set, Tuple

from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework import serializers, views, viewsets
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator

from .docstring_parser import parse_docstring


class CoreSchemaGenerator(SchemaGenerator):
    """
    Расширенный генератор схем API для создания более детальной документации.

    Улучшает стандартный SchemaGenerator из DRF, добавляя поддержку для
    более детальных метаданных, извлеченных из докстрингов и аннотаций.
    """

    def __init__(self, *args, **kwargs):
        """
        Инициализирует генератор схем.

        Аргументы:
            *args: Аргументы для передачи в родительский класс.
            **kwargs: Именованные аргументы для передачи в родительский класс.
        """
        super().__init__(*args, **kwargs)
        self.view_schemas = {}

    def get_schema(self, request=None, public=False):
        """
        Возвращает схему API на основе зарегистрированных представлений.

        Аргументы:
            request: HTTP-запрос, используемый для определения доступных URL-шаблонов и фильтрации.
            public: Если True, включает только схемы, помеченные как общедоступные.

        Возвращает:
            Словарь со схемой API.
        """
        schema = super().get_schema(request, public)

        # Дополнительные метаданные для схемы
        schema.update({
            'info': {
                'title': 'CRM API',
                'description': 'API для CRM-системы',
                'version': '0.1.0',
                'contact': {
                    'name': 'Команда разработки',
                    'email': 'dev@example.com'
                },
                'license': {
                    'name': 'Проприетарная лицензия',
                    'url': 'https://example.com/license'
                }
            }
        })

        # Дополнение компонентов схемы
        self._add_extra_schemas(schema)
        self._add_extra_examples(schema)

        return schema

    def _add_extra_schemas(self, schema: Dict[str, Any]) -> None:
        """
        Добавляет дополнительные компоненты к схеме.

        Аргументы:
            schema: Схема для дополнения.
        """
        if 'components' not in schema:
            schema['components'] = {}

        if 'schemas' not in schema['components']:
            schema['components']['schemas'] = {}

        # Здесь можно добавить дополнительные схемы компонентов

    def _add_extra_examples(self, schema: Dict[str, Any]) -> None:
        """
        Добавляет примеры к схеме API.

        Аргументы:
            schema: Схема для дополнения.
        """
        if 'components' not in schema:
            schema['components'] = {}

        if 'examples' not in schema['components']:
            schema['components']['examples'] = {}

        # Добавление примеров для общих типов ответов
        schema['components']['examples'].update({
            'ValidationError': {
                'summary': 'Ошибка валидации',
                'value': {
                    'error': 'Validation Error',
                    'details': {
                        'field_name': [
                            'Это поле обязательно.'
                        ]
                    }
                }
            },
            'AuthError': {
                'summary': 'Ошибка аутентификации',
                'value': {
                    'error': 'Authentication Error',
                    'details': 'Учетные данные не предоставлены.'
                }
            },
            'NotFoundError': {
                'summary': 'Ресурс не найден',
                'value': {
                    'error': 'Not Found',
                    'details': 'Запрашиваемый ресурс не найден.'
                }
            }
        })

    def get_paths(self, request=None):
        """
        Возвращает пути API с дополнительной информацией.

        Аргументы:
            request: HTTP-запрос для определения шаблонов URL.

        Возвращает:
            Словарь с путями API.
        """
        paths = super().get_paths(request)

        # Дополнение путей дополнительной информацией из докстрингов
        for path, path_item in paths.items():
            self._enhance_path_from_docstrings(path, path_item)

        return paths

    def _enhance_path_from_docstrings(self, path: str, path_item: Dict[str, Any]) -> None:
        """
        Улучшает информацию о пути API с помощью докстрингов.

        Аргументы:
            path: URL-путь.
            path_item: Словарь с информацией о пути.
        """
        for method, operation in path_item.items():
            if method in ('get', 'post', 'put', 'patch', 'delete'):
                view_name = operation.get('operationId', '').split('_')[0]
                if view_name in self.view_schemas:
                    view_schema = self.view_schemas[view_name]
                    docstring_info = view_schema.get('docstring', {})

                    # Дополнение описания операции
                    if 'description' not in operation and 'description' in docstring_info:
                        operation['description'] = docstring_info['description']

                    # Дополнение параметров
                    if 'params' in docstring_info:
                        self._add_parameters_from_docstring(operation, docstring_info['params'])

                    # Дополнение ответов
                    if 'returns' in docstring_info:
                        self._add_responses_from_docstring(operation, docstring_info['returns'])

    def _add_parameters_from_docstring(self, operation: Dict[str, Any], params: List[Dict[str, str]]) -> None:
        """
        Добавляет параметры из докстринга к операции API.

        Аргументы:
            operation: Словарь операции API.
            params: Список параметров из докстринга.
        """
        if 'parameters' not in operation:
            operation['parameters'] = []

        for param in params:
            # Проверка, существует ли уже такой параметр
            exists = any(p['name'] == param['name'] for p in operation['parameters'])
            if not exists:
                param_schema = {
                    'name': param['name'],
                    'in': 'query',  # По умолчанию считаем параметром запроса
                    'description': param['description'],
                    'required': False,
                    'schema': {
                        'type': 'string'  # По умолчанию считаем строкой
                    }
                }

                # Определение типа параметра по его описанию
                if param.get('type'):
                    type_info = param['type'].lower()
                    if 'int' in type_info:
                        param_schema['schema']['type'] = 'integer'
                    elif 'float' in type_info or 'double' in type_info:
                        param_schema['schema']['type'] = 'number'
                    elif 'bool' in type_info:
                        param_schema['schema']['type'] = 'boolean'
                    elif 'array' in type_info or 'list' in type_info:
                        param_schema['schema']['type'] = 'array'
                        param_schema['schema']['items'] = {'type': 'string'}
                    elif 'object' in type_info or 'dict' in type_info:
                        param_schema['schema']['type'] = 'object'

                operation['parameters'].append(param_schema)

    def _add_responses_from_docstring(self, operation: Dict[str, Any], returns: Dict[str, str]) -> None:
        """
        Добавляет информацию о возвращаемых значениях из докстринга.

        Аргументы:
            operation: Словарь операции API.
            returns: Информация о возвращаемых значениях из докстринга.
        """
        if 'responses' not in operation:
            operation['responses'] = {}

        # Добавление дополнительного описания успешного ответа
        if '200' in operation['responses'] and returns.get('description'):
            operation['responses']['200']['description'] = returns['description']


class EnhancedAutoSchema(AutoSchema):
    """
    Расширенная схема для представлений API.

    Добавляет поддержку для более детальных описаний действий API
    на основе докстрингов и аннотаций.
    """

    def get_operation(self, path, method):
        """
        Получает операцию для пути и метода.

        Аргументы:
            path: URL-путь.
            method: HTTP-метод.

        Возвращает:
            Словарь с информацией об операции.
        """
        operation = super().get_operation(path, method)

        # Получение докстринга метода API
        view = self.view
        method_name = getattr(view, 'action', method.lower())
        method_docstring = None

        # Для ViewSet ищем метод действия
        if hasattr(view, method_name):
            method_func = getattr(view, method_name)
            method_docstring = parse_docstring(method_func)
        # Для APIView ищем метод HTTP
        elif hasattr(view, method.lower()):
            method_func = getattr(view, method.lower())
            method_docstring = parse_docstring(method_func)

        # Дополнение операции информацией из докстринга
        if method_docstring:
            if 'description' not in operation and method_docstring.get('description'):
                operation['description'] = method_docstring['description']

            # Добавление тегов на основе модуля представления
            module_name = view.__module__.split('.')[-2]  # Предполагаем структуру app_name.api.views
            if module_name and 'tags' not in operation:
                operation['tags'] = [module_name.capitalize()]

        return operation

    def get_request_body(self, path, method):
        """
        Получает схему тела запроса.

        Аргументы:
            path: URL-путь.
            method: HTTP-метод.

        Возвращает:
            Словарь со схемой тела запроса.
        """
        request_body = super().get_request_body(path, method)

        # Если есть сериализатор, добавляем информацию из его докстрингов
        if hasattr(self.view, 'get_serializer'):
            serializer = self.view.get_serializer()
            serializer_class = serializer.__class__
            serializer_docstring = parse_docstring(serializer_class)

            if serializer_docstring.get('description') and request_body:
                request_body['description'] = serializer_docstring['description']

        return request_body

    def get_responses(self, path, method):
        """
        Получает схемы ответов API.

        Аргументы:
            path: URL-путь.
            method: HTTP-метод.

        Возвращает:
            Словарь со схемами ответов.
        """
        responses = super().get_responses(path, method)

        # Добавление типовых ответов для ошибок
        error_responses = {
            '400': {
                'description': 'Некорректный запрос',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        },
                        'examples': {
                            'validation_error': {'$ref': '#/components/examples/ValidationError'}
                        }
                    }
                }
            },
            '401': {
                'description': 'Не авторизован',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'details': {'type': 'string'}
                            }
                        },
                        'examples': {
                            'auth_error': {'$ref': '#/components/examples/AuthError'}
                        }
                    }
                }
            },
            '404': {
                'description': 'Ресурс не найден',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'details': {'type': 'string'}
                            }
                        },
                        'examples': {
                            'not_found': {'$ref': '#/components/examples/NotFoundError'}
                        }
                    }
                }
            }
        }

        # Добавление типовых ответов, если они не определены
        for status_code, response_schema in error_responses.items():
            if status_code not in responses:
                responses[status_code] = response_schema

        return responses
"""
Обработчики исключений для REST API.

Этот модуль предоставляет кастомные обработчики исключений для стандартизации
обработки различных типов ошибок в API.
"""

from typing import Dict, Any, Optional

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist,
)
from django.db import IntegrityError, DatabaseError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    APIException,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Кастомный обработчик исключений для REST framework.

    Расширяет стандартный обработчик исключений REST framework для обработки
    дополнительных типов исключений и предоставления более детальных сообщений об ошибках.

    Args:
        exc: Объект исключения.
        context: Контекст исключения.

    Returns:
        Response: Объект ответа с деталями ошибки или None, если исключение не обработано.
    """
    # Сначала вызываем стандартный обработчик исключений REST framework
    response = exception_handler(exc, context)

    # Если ответ уже обработан DRF, кастомизируем его
    if response is not None:
        response.data = {
            'error': str(exc),
            'details': response.data
        }
        return response

    # Обработка Django ValidationError
    if isinstance(exc, DjangoValidationError):
        return handle_django_validation_error(exc)

    # Обработка ошибок базы данных
    if isinstance(exc, IntegrityError):
        return handle_integrity_error(exc)
    if isinstance(exc, DatabaseError):
        return handle_database_error(exc)

    # Обработка ошибок доступа
    if isinstance(exc, DjangoPermissionDenied):
        return handle_permission_denied(exc)

    # Обработка ошибок 404
    if isinstance(exc, (Http404, ObjectDoesNotExist)):
        return handle_not_found(exc)

    # Если дошли сюда, значит это необработанное исключение
    return None


def handle_django_validation_error(exc: DjangoValidationError) -> Response:
    """
    Обрабатывает Django ValidationError.

    Преобразует Django ValidationError в стандартный формат.

    Args:
        exc: Исключение ValidationError.

    Returns:
        Response: Объект ответа с деталями ошибки.
    """
    # Преобразуем Django ValidationError в формат DRF ValidationError
    detail = {}

    if hasattr(exc, 'error_dict'):
        for field, errors in exc.error_dict.items():
            detail[field] = [str(e) for e in errors]
    else:
        detail['non_field_errors'] = [str(e) for e in exc.error_list]

    return Response(
        {
            'error': 'Ошибка валидации',
            'details': detail
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def handle_integrity_error(exc: IntegrityError) -> Response:
    """
    Обрабатывает IntegrityError.

    Преобразует IntegrityError в стандартный формат.

    Args:
        exc: Исключение IntegrityError.

    Returns:
        Response: Объект ответа с деталями ошибки.
    """
    error_message = str(exc)
    details = {'db_error': error_message}

    # Попытка определить более конкретный тип ошибки на основе сообщения
    if 'unique constraint' in error_message.lower() or 'unique violation' in error_message.lower():
        error_type = 'Нарушение ограничения уникальности'
    elif 'foreign key constraint' in error_message.lower() or 'foreign key violation' in error_message.lower():
        error_type = 'Нарушение внешнего ключа'
    elif 'check constraint' in error_message.lower() or 'check violation' in error_message.lower():
        error_type = 'Нарушение ограничения проверки'
    elif 'not null constraint' in error_message.lower() or 'not null violation' in error_message.lower():
        error_type = 'Нарушение ограничения NOT NULL'
    else:
        error_type = 'Ошибка целостности базы данных'

    return Response(
        {
            'error': error_type,
            'details': details
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def handle_database_error(exc: DatabaseError) -> Response:
    """
    Обрабатывает DatabaseError.

    Преобразует DatabaseError в стандартный формат.

    Args:
        exc: Исключение DatabaseError.

    Returns:
        Response: Объект ответа с деталями ошибки.
    """
    return Response(
        {
            'error': 'Ошибка базы данных',
            'details': {
                'db_error': str(exc)
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def handle_permission_denied(exc: DjangoPermissionDenied) -> Response:
    """
    Обрабатывает PermissionDenied.

    Преобразует PermissionDenied в стандартный формат.

    Args:
        exc: Исключение PermissionDenied.

    Returns:
        Response: Объект ответа с деталями ошибки.
    """
    return Response(
        {
            'error': 'Доступ запрещен',
            'details': {
                'message': str(exc) or 'У вас нет разрешения на выполнение этого действия.'
            }
        },
        status=status.HTTP_403_FORBIDDEN
    )


def handle_not_found(exc: Exception) -> Response:
    """
    Обрабатывает ошибки 404 (NotFound, ObjectDoesNotExist, Http404).

    Преобразует ошибки 404 в стандартный формат.

    Args:
        exc: Исключение NotFound или ObjectDoesNotExist.

    Returns:
        Response: Объект ответа с деталями ошибки.
    """
    return Response(
        {
            'error': 'Не найдено',
            'details': {
                'message': str(exc) or 'Запрашиваемый ресурс не найден.'
            }
        },
        status=status.HTTP_404_NOT_FOUND
    )
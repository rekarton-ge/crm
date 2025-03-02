"""
Custom exception handlers for REST framework.

This module provides custom exception handlers for handling different types
of exceptions in a standardized way across the API.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework.

    This handler extends the default REST framework exception handler to handle
    additional exceptions and provide more detailed error messages.

    Args:
        exc: The exception object.
        context: The context of the exception.

    Returns:
        Response object with error details or None if the exception is not handled.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is already handled by DRF, customize it
    if response is not None:
        response.data = {
            'error': str(exc),
            'details': response.data
        }
        return response

    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        return handle_django_validation_error(exc)

    # Handle IntegrityError (e.g., unique constraint violations)
    if isinstance(exc, IntegrityError):
        return handle_integrity_error(exc)

    # If we got here, it's an unhandled exception
    return None


def handle_django_validation_error(exc):
    """
    Handle Django ValidationError.

    Convert Django ValidationError to a standard format.

    Args:
        exc: The ValidationError exception.

    Returns:
        Response object with error details.
    """
    # Convert Django ValidationError to DRF ValidationError format
    detail = {}

    if hasattr(exc, 'error_dict'):
        for field, errors in exc.error_dict.items():
            detail[field] = [str(e) for e in errors]
    else:
        detail['non_field_errors'] = [str(e) for e in exc.error_list]

    return Response(
        {
            'error': 'Validation Error',
            'details': detail
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def handle_integrity_error(exc):
    """
    Handle IntegrityError.

    Convert IntegrityError to a standard format.

    Args:
        exc: The IntegrityError exception.

    Returns:
        Response object with error details.
    """
    return Response(
        {
            'error': 'Database Integrity Error',
            'details': {
                'db_error': str(exc)
            }
        },
        status=status.HTTP_400_BAD_REQUEST
    )
"""
Обработчики ошибок для операций обработки данных.

Этот модуль предоставляет обработчики ошибок, которые могут возникать
во время импорта, экспорта и обработки данных, включая функциональность
для логирования, уведомления и восстановления после ошибок.
"""

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from django.db import transaction
from django.db.models import Model

# Настройка логгера
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок при обработке данных."""

    INFO = "info"  # Информационное сообщение, не является ошибкой
    WARNING = "warning"  # Предупреждение, обработка может быть продолжена
    ERROR = "error"  # Ошибка, обработка может быть продолжена с пропуском текущего элемента
    CRITICAL = "critical"  # Критическая ошибка, обработка должна быть остановлена


class ErrorCategory(Enum):
    """Категории ошибок обработки данных."""

    VALIDATION = "validation"  # Ошибки валидации данных
    DATA_FORMAT = "data_format"  # Ошибки формата данных
    MISSING_DATA = "missing_data"  # Отсутствующие данные
    DUPLICATE = "duplicate"  # Дублирование данных
    TYPE_ERROR = "type_error"  # Ошибки типов данных
    PERMISSION = "permission"  # Ошибки доступа
    DATABASE = "database"  # Ошибки базы данных
    SYSTEM = "system"  # Системные ошибки
    UNKNOWN = "unknown"  # Неизвестные ошибки


@dataclass
class ProcessingError:
    """
    Класс для представления ошибки обработки данных.

    Содержит информацию об ошибке, включая сообщение, категорию,
    серьезность, строку/индекс данных, поле и исходное исключение.
    """

    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    row_index: Optional[int] = None
    field_name: Optional[str] = None
    exception: Optional[Exception] = None
    trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Постобработка после инициализации объекта.

        Если trace не указан явно, но есть исключение, автоматически
        создает трассировку стека для исключения.
        """
        if self.trace is None and self.exception is not None:
            self.trace = ''.join(traceback.format_exception(
                type(self.exception),
                self.exception,
                self.exception.__traceback__
            ))

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует ошибку в словарь для сериализации.

        Returns:
            Dict[str, Any]: Словарь с информацией об ошибке
        """
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'row_index': self.row_index,
            'field_name': self.field_name,
            'trace': self.trace,
            'context': self.context
        }

    @classmethod
    def from_exception(cls,
                       exception: Exception,
                       category: ErrorCategory = ErrorCategory.UNKNOWN,
                       severity: ErrorSeverity = ErrorSeverity.ERROR,
                       row_index: Optional[int] = None,
                       field_name: Optional[str] = None,
                       context: Optional[Dict[str, Any]] = None) -> 'ProcessingError':
        """
        Создает объект ошибки из исключения.

        Args:
            exception: Исходное исключение
            category: Категория ошибки
            severity: Серьезность ошибки
            row_index: Индекс строки, где произошла ошибка
            field_name: Имя поля, где произошла ошибка
            context: Дополнительный контекст ошибки

        Returns:
            ProcessingError: Объект ошибки
        """
        return cls(
            message=str(exception),
            category=category,
            severity=severity,
            row_index=row_index,
            field_name=field_name,
            exception=exception,
            context=context or {}
        )


@dataclass
class ProcessingResult:
    """
    Результат обработки данных.

    Содержит информацию о результате обработки, включая успешность,
    количество обработанных и пропущенных элементов, и список ошибок.
    """

    success: bool = True
    processed_count: int = 0
    skipped_count: int = 0
    success_count: int = 0
    errors: List[ProcessingError] = field(default_factory=list)
    warnings: List[ProcessingError] = field(default_factory=list)
    created_objects: List[Any] = field(default_factory=list)
    updated_objects: List[Any] = field(default_factory=list)

    def add_error(self, error: ProcessingError) -> None:
        """
        Добавляет ошибку в результат.

        Args:
            error: Ошибка для добавления
        """
        # Если ошибка критическая, помечаем весь результат как неуспешный
        if error.severity == ErrorSeverity.CRITICAL:
            self.success = False

        # Определяем, куда добавить ошибку (в errors или warnings)
        if error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.errors.append(error)
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)

        # Логируем ошибку
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Критическая ошибка: {error.message}", exc_info=error.exception)
        elif error.severity == ErrorSeverity.ERROR:
            logger.error(f"Ошибка: {error.message}", exc_info=error.exception)
        elif error.severity == ErrorSeverity.WARNING:
            logger.warning(f"Предупреждение: {error.message}")

    def has_critical_errors(self) -> bool:
        """
        Проверяет наличие критических ошибок.

        Returns:
            bool: True, если есть критические ошибки, иначе False
        """
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует результат в словарь для сериализации.

        Returns:
            Dict[str, Any]: Словарь с информацией о результате
        """
        return {
            'success': self.success,
            'processed_count': self.processed_count,
            'skipped_count': self.skipped_count,
            'success_count': self.success_count,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'created_count': len(self.created_objects),
            'updated_count': len(self.updated_objects)
        }

    def merge(self, other: 'ProcessingResult') -> None:
        """
        Объединяет данный результат с другим результатом.

        Полезно при параллельной обработке данных, когда нужно
        объединить результаты отдельных процессов.

        Args:
            other: Другой результат для объединения
        """
        self.success = self.success and other.success
        self.processed_count += other.processed_count
        self.skipped_count += other.skipped_count
        self.success_count += other.success_count
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.created_objects.extend(other.created_objects)
        self.updated_objects.extend(other.updated_objects)


class ErrorHandler:
    """
    Базовый класс для обработчиков ошибок.

    Определяет интерфейс для обработки ошибок, возникающих
    во время операций обработки данных.
    """

    def handle_error(self, error: ProcessingError, result: ProcessingResult) -> bool:
        """
        Обрабатывает ошибку.

        Args:
            error: Ошибка для обработки
            result: Результат обработки данных, в который нужно добавить ошибку

        Returns:
            bool: True, если обработка может быть продолжена, иначе False
        """
        result.add_error(error)

        # Если ошибка критическая, останавливаем обработку
        return error.severity != ErrorSeverity.CRITICAL

    def handle_exception(self,
                         exception: Exception,
                         category: ErrorCategory = ErrorCategory.UNKNOWN,
                         severity: ErrorSeverity = ErrorSeverity.ERROR,
                         row_index: Optional[int] = None,
                         field_name: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None,
                         result: Optional[ProcessingResult] = None) -> bool:
        """
        Обрабатывает исключение.

        Args:
            exception: Исключение для обработки
            category: Категория ошибки
            severity: Серьезность ошибки
            row_index: Индекс строки, где произошла ошибка
            field_name: Имя поля, где произошла ошибка
            context: Дополнительный контекст ошибки
            result: Результат обработки данных, в который нужно добавить ошибку

        Returns:
            bool: True, если обработка может быть продолжена, иначе False
        """
        # Создаем объект ошибки из исключения
        error = ProcessingError.from_exception(
            exception=exception,
            category=category,
            severity=severity,
            row_index=row_index,
            field_name=field_name,
            context=context or {}
        )

        # Если результат не передан, просто логируем ошибку
        if result is None:
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(f"Критическая ошибка: {error.message}", exc_info=exception)
            elif severity == ErrorSeverity.ERROR:
                logger.error(f"Ошибка: {error.message}", exc_info=exception)
            elif severity == ErrorSeverity.WARNING:
                logger.warning(f"Предупреждение: {error.message}")

            # Возвращаем True, если обработка может быть продолжена
            return severity != ErrorSeverity.CRITICAL

        # Иначе обрабатываем ошибку с помощью метода handle_error
        return self.handle_error(error, result)


class DefaultErrorHandler(ErrorHandler):
    """
    Обработчик ошибок по умолчанию.

    Реализует стандартное поведение обработки ошибок: логирование,
    добавление в результат и решение о продолжении обработки.
    """
    pass


class TransactionErrorHandler(ErrorHandler):
    """
    Обработчик ошибок с использованием транзакций.

    Обеспечивает откат транзакций при возникновении критических ошибок,
    что позволяет сохранять целостность данных.
    """

    def handle_error(self, error: ProcessingError, result: ProcessingResult) -> bool:
        """
        Обрабатывает ошибку с использованием транзакций.

        Args:
            error: Ошибка для обработки
            result: Результат обработки данных, в который нужно добавить ошибку

        Returns:
            bool: True, если обработка может быть продолжена, иначе False
        """
        result.add_error(error)

        # Если ошибка критическая, отменяем транзакцию
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Отмена транзакции из-за критической ошибки: {error.message}")
            transaction.set_rollback(True)
            return False

        # Если ошибка некритическая, продолжаем обработку
        return True


class ErrorHandlerFactory:
    """
    Фабрика для создания обработчиков ошибок.

    Предоставляет методы для создания различных типов обработчиков ошибок
    в зависимости от требований к обработке данных.
    """

    @staticmethod
    def create_default_handler() -> ErrorHandler:
        """
        Создает обработчик ошибок по умолчанию.

        Returns:
            ErrorHandler: Созданный обработчик ошибок
        """
        return DefaultErrorHandler()

    @staticmethod
    def create_transaction_handler() -> ErrorHandler:
        """
        Создает обработчик ошибок с поддержкой транзакций.

        Returns:
            ErrorHandler: Созданный обработчик ошибок
        """
        return TransactionErrorHandler()


# Создаем глобальный обработчик ошибок по умолчанию
default_error_handler = ErrorHandlerFactory.create_default_handler()


def handle_processing_errors(process_func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок в функциях обработки данных.

    Args:
        process_func: Функция для декорирования

    Returns:
        Callable: Декорированная функция

    Examples:
        ```python
        @handle_processing_errors
        def process_data(data):
            # Обработка данных
            return result
        ```
    """

    def wrapper(*args, **kwargs) -> ProcessingResult:
        result = ProcessingResult()

        try:
            # Вызываем оригинальную функцию
            process_result = process_func(*args, **kwargs)

            # Если функция вернула результат обработки, используем его
            if isinstance(process_result, ProcessingResult):
                return process_result

            # Иначе создаем новый результат
            result.success = True
            result.processed_count = 1
            result.success_count = 1

            # Если функция вернула объект, добавляем его в результат
            if isinstance(process_result, Model):
                if hasattr(process_result, '_state') and process_result._state.adding:
                    result.created_objects.append(process_result)
                else:
                    result.updated_objects.append(process_result)

            return result
        except Exception as e:
            # В случае исключения создаем ошибку и добавляем в результат
            error = ProcessingError.from_exception(
                exception=e,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.CRITICAL
            )
            result.add_error(error)
            result.success = False
            return result

    return wrapper


def with_error_handling(error_handler: Optional[ErrorHandler] = None) -> Callable:
    """
    Декоратор для обработки ошибок с указанным обработчиком.

    Args:
        error_handler: Обработчик ошибок для использования

    Returns:
        Callable: Декоратор для функции

    Examples:
        ```python
        @with_error_handling(TransactionErrorHandler())
        def process_data(data):
            # Обработка данных
            return result
        ```
    """

    def decorator(process_func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> ProcessingResult:
            # Используем указанный обработчик или обработчик по умолчанию
            handler = error_handler or default_error_handler
            result = ProcessingResult()

            try:
                # Вызываем оригинальную функцию
                process_result = process_func(*args, **kwargs)

                # Если функция вернула результат обработки, используем его
                if isinstance(process_result, ProcessingResult):
                    return process_result

                # Иначе создаем новый результат
                result.success = True
                result.processed_count = 1
                result.success_count = 1

                # Если функция вернула объект, добавляем его в результат
                if isinstance(process_result, Model):
                    if hasattr(process_result, '_state') and process_result._state.adding:
                        result.created_objects.append(process_result)
                    else:
                        result.updated_objects.append(process_result)

                return result
            except Exception as e:
                # В случае исключения используем обработчик ошибок
                handler.handle_exception(
                    exception=e,
                    result=result
                )
                return result

        return wrapper

    return decorator
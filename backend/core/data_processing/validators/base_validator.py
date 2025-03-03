"""
Базовый валидатор данных.

Этот модуль содержит абстрактный базовый класс для валидаторов данных,
который определяет общий интерфейс и функциональность для всех валидаторов.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from core.data_processing.error_handlers import (
    ErrorCategory,
    ErrorHandler,
    ErrorHandlerFactory,
    ErrorSeverity,
    ProcessingError,
    ProcessingResult
)


class ValidationError:
    """
    Класс для представления ошибки валидации.

    Содержит информацию об ошибке валидации, включая сообщение,
    имя поля, индекс строки и т.д.
    """

    def __init__(self,
                 message: str,
                 field_name: Optional[str] = None,
                 row_index: Optional[int] = None,
                 col_index: Optional[int] = None,
                 code: Optional[str] = None,
                 severity: ErrorSeverity = ErrorSeverity.ERROR):
        """
        Инициализирует ошибку валидации с указанными параметрами.

        Args:
            message: Сообщение об ошибке.
            field_name: Имя поля, в котором произошла ошибка.
            row_index: Индекс строки, в которой произошла ошибка.
            col_index: Индекс столбца, в котором произошла ошибка.
            code: Код ошибки.
            severity: Серьезность ошибки.
        """
        self.message = message
        self.field_name = field_name
        self.row_index = row_index
        self.col_index = col_index
        self.code = code
        self.severity = severity

    def __str__(self) -> str:
        """
        Возвращает строковое представление ошибки.

        Returns:
            str: Строковое представление ошибки.
        """
        parts = []

        if self.field_name:
            parts.append(f"Поле '{self.field_name}'")

        if self.row_index is not None:
            if self.col_index is not None:
                parts.append(f"в строке {self.row_index + 1}, столбце {self.col_index + 1}")
            else:
                parts.append(f"в строке {self.row_index + 1}")

        parts.append(self.message)

        return ": ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует ошибку в словарь для сериализации.

        Returns:
            Dict[str, Any]: Словарь с информацией об ошибке.
        """
        return {
            'message': self.message,
            'field_name': self.field_name,
            'row_index': self.row_index,
            'col_index': self.col_index,
            'code': self.code,
            'severity': self.severity.value
        }

    def to_processing_error(self) -> ProcessingError:
        """
        Преобразует ошибку валидации в ошибку обработки.

        Returns:
            ProcessingError: Ошибка обработки.
        """
        return ProcessingError(
            message=self.message,
            category=ErrorCategory.VALIDATION,
            severity=self.severity,
            row_index=self.row_index,
            field_name=self.field_name,
            context={
                'col_index': self.col_index,
                'code': self.code
            }
        )


class ValidationResult:
    """
    Класс для представления результата валидации.

    Содержит информацию о результате валидации, включая список ошибок,
    предупреждений и информационных сообщений.
    """

    def __init__(self):
        """
        Инициализирует результат валидации.
        """
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.infos: List[ValidationError] = []

    def add_error(self,
                  message: str,
                  field_name: Optional[str] = None,
                  row_index: Optional[int] = None,
                  col_index: Optional[int] = None,
                  code: Optional[str] = None) -> None:
        """
        Добавляет ошибку в результат валидации.

        Args:
            message: Сообщение об ошибке.
            field_name: Имя поля, в котором произошла ошибка.
            row_index: Индекс строки, в которой произошла ошибка.
            col_index: Индекс столбца, в котором произошла ошибка.
            code: Код ошибки.
        """
        error = ValidationError(
            message=message,
            field_name=field_name,
            row_index=row_index,
            col_index=col_index,
            code=code,
            severity=ErrorSeverity.ERROR
        )
        self.errors.append(error)

    def add_warning(self,
                    message: str,
                    field_name: Optional[str] = None,
                    row_index: Optional[int] = None,
                    col_index: Optional[int] = None,
                    code: Optional[str] = None) -> None:
        """
        Добавляет предупреждение в результат валидации.

        Args:
            message: Сообщение о предупреждении.
            field_name: Имя поля, в котором произошло предупреждение.
            row_index: Индекс строки, в которой произошло предупреждение.
            col_index: Индекс столбца, в котором произошло предупреждение.
            code: Код предупреждения.
        """
        warning = ValidationError(
            message=message,
            field_name=field_name,
            row_index=row_index,
            col_index=col_index,
            code=code,
            severity=ErrorSeverity.WARNING
        )
        self.warnings.append(warning)

    def add_info(self,
                 message: str,
                 field_name: Optional[str] = None,
                 row_index: Optional[int] = None,
                 col_index: Optional[int] = None,
                 code: Optional[str] = None) -> None:
        """
        Добавляет информационное сообщение в результат валидации.

        Args:
            message: Информационное сообщение.
            field_name: Имя поля, к которому относится сообщение.
            row_index: Индекс строки, к которой относится сообщение.
            col_index: Индекс столбца, к которому относится сообщение.
            code: Код сообщения.
        """
        info = ValidationError(
            message=message,
            field_name=field_name,
            row_index=row_index,
            col_index=col_index,
            code=code,
            severity=ErrorSeverity.INFO
        )
        self.infos.append(info)

    def add_validation_error(self, error: ValidationError) -> None:
        """
        Добавляет готовую ошибку валидации в результат.

        Args:
            error: Ошибка валидации.
        """
        if error.severity == ErrorSeverity.ERROR:
            self.errors.append(error)
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)
        elif error.severity == ErrorSeverity.INFO:
            self.infos.append(error)

    def merge(self, other: 'ValidationResult') -> None:
        """
        Объединяет текущий результат с другим результатом валидации.

        Args:
            other: Другой результат валидации.
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.infos.extend(other.infos)

    def is_valid(self) -> bool:
        """
        Проверяет, прошла ли валидация успешно.

        Returns:
            bool: True, если нет ошибок, иначе False.
        """
        return len(self.errors) == 0

    def has_warnings(self) -> bool:
        """
        Проверяет, есть ли предупреждения.

        Returns:
            bool: True, если есть предупреждения, иначе False.
        """
        return len(self.warnings) > 0

    def has_infos(self) -> bool:
        """
        Проверяет, есть ли информационные сообщения.

        Returns:
            bool: True, если есть информационные сообщения, иначе False.
        """
        return len(self.infos) > 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует результат валидации в словарь для сериализации.

        Returns:
            Dict[str, Any]: Словарь с информацией о результате валидации.
        """
        return {
            'is_valid': self.is_valid(),
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'infos': [info.to_dict() for info in self.infos]
        }

    def to_processing_result(self) -> ProcessingResult:
        """
        Преобразует результат валидации в результат обработки.

        Returns:
            ProcessingResult: Результат обработки.
        """
        result = ProcessingResult()

        # Копируем статус
        result.success = self.is_valid()

        # Добавляем ошибки
        for error in self.errors:
            result.add_error(error.to_processing_error())

        # Добавляем предупреждения
        for warning in self.warnings:
            result.warnings.append(warning.to_processing_error())

        return result


class BaseValidator(ABC):
    """
    Абстрактный базовый класс для всех валидаторов данных.

    Определяет общий интерфейс и функциональность для валидации данных
    различных типов и форматов.
    """

    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        """
        Инициализирует валидатор с указанным обработчиком ошибок.

        Args:
            error_handler: Обработчик ошибок для использования.
        """
        self.error_handler = error_handler or ErrorHandlerFactory.create_default_handler()

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """
        Валидирует данные.

        Этот метод должен быть реализован в подклассах.

        Args:
            data: Данные для валидации.

        Returns:
            ValidationResult: Результат валидации.
        """
        pass

    def validate_and_process(self, data: Any) -> ProcessingResult:
        """
        Валидирует данные и преобразует результат в результат обработки.

        Args:
            data: Данные для валидации.

        Returns:
            ProcessingResult: Результат обработки.
        """
        validation_result = self.validate(data)
        return validation_result.to_processing_result()


class CompositeValidator(BaseValidator):
    """
    Валидатор, объединяющий несколько других валидаторов.

    Позволяет создавать цепочки валидаторов для последовательной
    проверки данных на соответствие различным критериям.
    """

    def __init__(self, validators: List[BaseValidator], error_handler: Optional[ErrorHandler] = None):
        """
        Инициализирует составной валидатор с указанными валидаторами.

        Args:
            validators: Список валидаторов для использования.
            error_handler: Обработчик ошибок для использования.
        """
        super().__init__(error_handler)
        self.validators = validators

    def validate(self, data: Any) -> ValidationResult:
        """
        Валидирует данные с использованием всех валидаторов.

        Args:
            data: Данные для валидации.

        Returns:
            ValidationResult: Объединенный результат валидации.
        """
        result = ValidationResult()

        # Запускаем все валидаторы и объединяем результаты
        for validator in self.validators:
            validator_result = validator.validate(data)
            result.merge(validator_result)

        return result

    def add_validator(self, validator: BaseValidator) -> None:
        """
        Добавляет валидатор в список.

        Args:
            validator: Валидатор для добавления.
        """
        self.validators.append(validator)
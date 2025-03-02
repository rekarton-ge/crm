"""
Базовый импортер данных.

Этот модуль содержит абстрактный базовый класс для импортеров данных,
который определяет общий интерфейс и функциональность для всех импортеров.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.db import models, transaction
from django.db.models import Model

from core.data_processing.error_handlers import (
    ErrorCategory,
    ErrorHandler,
    ErrorHandlerFactory,
    ErrorSeverity,
    ProcessingError,
    ProcessingResult
)

# Настройка логгера
logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    """
    Абстрактный базовый класс для всех импортеров данных.

    Определяет общий интерфейс и функциональность для импорта данных
    из различных форматов, таких как CSV, Excel и JSON, в модели Django.
    """

    # Название формата импорта (переопределяется в подклассах)
    format_name = "base"

    # Список поддерживаемых расширений файлов (переопределяется в подклассах)
    supported_extensions = []

    def __init__(self,
                 model_class: Type[Model],
                 mapping: Optional[Dict[str, str]] = None,
                 default_values: Optional[Dict[str, Any]] = None,
                 update_existing: bool = False,
                 unique_fields: Optional[List[str]] = None,
                 transform_functions: Optional[Dict[str, Callable]] = None,
                 skip_rows: int = 0,
                 max_rows: Optional[int] = None,
                 batch_size: int = 100,
                 error_handler: Optional[ErrorHandler] = None,
                 validate_before_save: bool = True,
                 use_transactions: bool = True):
        """
        Инициализирует импортер с указанными настройками.

        Args:
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            default_values: Словарь значений по умолчанию для полей модели.
            update_existing: Обновлять ли существующие записи.
            unique_fields: Список полей для идентификации существующих записей.
            transform_functions: Словарь функций для трансформации данных.
            skip_rows: Количество строк для пропуска с начала файла.
            max_rows: Максимальное количество строк для импорта.
            batch_size: Размер пакета для импорта.
            error_handler: Обработчик ошибок для использования.
            validate_before_save: Проводить ли валидацию перед сохранением.
            use_transactions: Использовать ли транзакции при импорте.
        """
        self.model_class = model_class
        self.mapping = mapping or {}
        self.default_values = default_values or {}
        self.update_existing = update_existing
        self.unique_fields = unique_fields or []
        self.transform_functions = transform_functions or {}
        self.skip_rows = skip_rows
        self.max_rows = max_rows
        self.batch_size = batch_size
        self.error_handler = error_handler or ErrorHandlerFactory.create_default_handler()
        self.validate_before_save = validate_before_save
        self.use_transactions = use_transactions

        # Список полей модели
        self.model_fields = [f.name for f in model_class._meta.fields]

        # Валидация настроек
        self._validate_settings()

    def _validate_settings(self) -> None:
        """
        Проверяет корректность настроек импортера.

        Raises:
            ValueError: Если настройки некорректны.
        """
        # Проверяем, что все поля в mapping существуют в модели
        for model_field in self.mapping.values():
            if model_field not in self.model_fields:
                raise ValueError(f"Поле '{model_field}' не найдено в модели {self.model_class.__name__}")

        # Проверяем, что все поля в default_values существуют в модели
        for field_name in self.default_values:
            if field_name not in self.model_fields:
                raise ValueError(f"Поле '{field_name}' не найдено в модели {self.model_class.__name__}")

        # Проверяем, что все поля в unique_fields существуют в модели
        for field_name in self.unique_fields:
            if field_name not in self.model_fields:
                raise ValueError(f"Поле '{field_name}' не найдено в модели {self.model_class.__name__}")

        # Проверяем, что все поля в transform_functions существуют в модели
        for field_name in self.transform_functions:
            if field_name not in self.model_fields:
                raise ValueError(f"Поле '{field_name}' не найдено в модели {self.model_class.__name__}")

        # Если update_existing=True, должны быть указаны unique_fields
        if self.update_existing and not self.unique_fields:
            raise ValueError("При update_existing=True должны быть указаны unique_fields")

    def transform_value(self, field_name: str, value: Any) -> Any:
        """
        Трансформирует значение поля перед импортом.

        Args:
            field_name: Имя поля модели.
            value: Значение для трансформации.

        Returns:
            Any: Трансформированное значение.
        """
        # Если есть функция трансформации для данного поля, применяем ее
        if field_name in self.transform_functions:
            try:
                return self.transform_functions[field_name](value)
            except Exception as e:
                logger.error(f"Ошибка при трансформации значения для поля '{field_name}': {str(e)}")
                # В случае ошибки трансформации возвращаем исходное значение
                return value

        # Если значение пустая строка, заменяем на None
        if value == "":
            return None

        return value

    def find_existing_object(self, data: Dict[str, Any]) -> Optional[Model]:
        """
        Ищет существующий объект по заданным уникальным полям.

        Args:
            data: Словарь данных импортируемой записи.

        Returns:
            Optional[Model]: Найденный объект или None, если объект не найден.
        """
        if not self.unique_fields:
            return None

        # Создаем словарь для фильтрации
        filter_kwargs = {}
        for field_name in self.unique_fields:
            if field_name in data:
                filter_kwargs[field_name] = data[field_name]

        # Если нет значений для уникальных полей, возвращаем None
        if not filter_kwargs:
            return None

        try:
            # Пытаемся найти объект
            return self.model_class.objects.get(**filter_kwargs)
        except self.model_class.DoesNotExist:
            return None
        except self.model_class.MultipleObjectsReturned:
            # Если найдено несколько объектов, возвращаем первый
            logger.warning(f"Найдено несколько объектов для {filter_kwargs}, используется первый")
            return self.model_class.objects.filter(**filter_kwargs).first()
        except Exception as e:
            logger.error(f"Ошибка при поиске существующего объекта: {str(e)}")
            return None

    def prepare_data_for_model(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подготавливает данные для импорта в модель.

        Args:
            row_data: Словарь данных импортируемой строки.

        Returns:
            Dict[str, Any]: Словарь подготовленных данных для модели.
        """
        # Создаем словарь данных для модели
        model_data = {}

        # Добавляем значения по умолчанию
        for field_name, value in self.default_values.items():
            model_data[field_name] = value

        # Добавляем данные из mapping
        for file_field, model_field in self.mapping.items():
            if file_field in row_data:
                # Трансформируем значение перед импортом
                value = self.transform_value(model_field, row_data[file_field])
                model_data[model_field] = value

        return model_data

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Валидирует данные перед созданием или обновлением объекта.

        Args:
            data: Словарь данных для модели.

        Returns:
            List[str]: Список ошибок валидации. Пустой список, если ошибок нет.
        """
        # Создаем экземпляр модели, но не сохраняем его
        instance = self.model_class(**data)

        # Используем встроенный метод full_clean для валидации
        try:
            instance.full_clean(exclude=['id'])
            return []
        except models.ValidationError as e:
            # Возвращаем список сообщений об ошибках
            errors = []
            for field, error_list in e.message_dict.items():
                errors.extend([f"{field}: {error}" for error in error_list])
            return errors

    def create_or_update_object(self, data: Dict[str, Any], row_index: int, result: ProcessingResult) -> Optional[
        Model]:
        """
        Создает новый объект или обновляет существующий.

        Args:
            data: Словарь данных для модели.
            row_index: Индекс строки в файле.
            result: Результат импорта для обновления.

        Returns:
            Optional[Model]: Созданный или обновленный объект, или None в случае ошибки.
        """
        try:
            # Валидация данных перед сохранением
            if self.validate_before_save:
                validation_errors = self.validate_data(data)
                if validation_errors:
                    error = ProcessingError(
                        message=f"Ошибка валидации данных: {'; '.join(validation_errors)}",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        row_index=row_index,
                        context={'data': data}
                    )
                    self.error_handler.handle_error(error, result)
                    return None

            # Проверяем, существует ли объект
            existing_object = None
            if self.update_existing:
                existing_object = self.find_existing_object(data)

            # Создаем или обновляем объект
            if existing_object and self.update_existing:
                # Обновляем существующий объект
                for field_name, value in data.items():
                    setattr(existing_object, field_name, value)
                existing_object.save()
                result.updated_objects.append(existing_object)
                logger.debug(f"Обновлен объект {self.model_class.__name__} (ID: {existing_object.pk})")
                return existing_object
            else:
                # Создаем новый объект
                new_object = self.model_class(**data)
                new_object.save()
                result.created_objects.append(new_object)
                logger.debug(f"Создан новый объект {self.model_class.__name__} (ID: {new_object.pk})")
                return new_object

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                row_index=row_index,
                context={'data': data},
                result=result
            )
            return None

    def import_row(self, row_data: Dict[str, Any], row_index: int, result: ProcessingResult) -> Optional[Model]:
        """
        Импортирует одну строку данных.

        Args:
            row_data: Словарь данных импортируемой строки.
            row_index: Индекс строки в файле.
            result: Результат импорта для обновления.

        Returns:
            Optional[Model]: Созданный или обновленный объект, или None в случае ошибки.
        """
        try:
            # Подготавливаем данные для модели
            model_data = self.prepare_data_for_model(row_data)

            # Создаем или обновляем объект
            result.processed_count += 1
            obj = self.create_or_update_object(model_data, row_index, result)

            if obj:
                result.success_count += 1
                return obj
            else:
                result.skipped_count += 1
                return None

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                row_index=row_index,
                context={'data': row_data},
                result=result
            )

            result.skipped_count += 1
            return None

    def process_data(self, data: List[Dict[str, Any]]) -> ProcessingResult:
        """
        Обрабатывает данные из файла и импортирует их в модель.

        Args:
            data: Список словарей с данными для импорта.

        Returns:
            ProcessingResult: Результат импорта.
        """
        result = ProcessingResult()

        # Пропускаем указанное количество строк с начала
        data = data[self.skip_rows:]

        # Ограничиваем количество строк, если задано
        if self.max_rows is not None:
            data = data[:self.max_rows]

        # Импортируем данные с использованием транзакции, если требуется
        if self.use_transactions:
            try:
                with transaction.atomic():
                    self._process_data_batch(data, result)

                    # Если есть критические ошибки, откатываем транзакцию
                    if result.has_critical_errors():
                        transaction.set_rollback(True)
                        logger.error("Импорт отменен из-за критических ошибок")
                        result.success = False
            except Exception as e:
                # Обрабатываем исключение
                self.error_handler.handle_exception(
                    exception=e,
                    category=ErrorCategory.DATABASE,
                    severity=ErrorSeverity.CRITICAL,
                    result=result
                )
                result.success = False
        else:
            # Обработка без транзакции
            self._process_data_batch(data, result)

        # Обновляем общий статус импорта
        result.success = not result.has_critical_errors()

        return result

    def _process_data_batch(self, data: List[Dict[str, Any]], result: ProcessingResult) -> None:
        """
        Обрабатывает пакет данных для импорта.

        Args:
            data: Список словарей с данными для импорта.
            result: Результат импорта для обновления.
        """
        # Импортируем каждую строку данных
        for i, row_data in enumerate(data):
            row_index = self.skip_rows + i
            self.import_row(row_data, row_index, result)

    @abstractmethod
    def read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Читает данные из файла.

        Этот метод должен быть реализован в подклассах.

        Args:
            file_path: Путь к файлу для чтения.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными из файла.
        """
        pass

    def import_file(self, file_path: str) -> ProcessingResult:
        """
        Импортирует данные из файла.

        Args:
            file_path: Путь к файлу для импорта.

        Returns:
            ProcessingResult: Результат импорта.
        """
        result = ProcessingResult()

        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                error = ProcessingError(
                    message=f"Файл не найден: {file_path}",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.CRITICAL
                )
                self.error_handler.handle_error(error, result)
                return result

            # Проверяем расширение файла
            _, ext = os.path.splitext(file_path)
            ext = ext.lower().lstrip('.')

            if self.supported_extensions and ext not in self.supported_extensions:
                error = ProcessingError(
                    message=f"Неподдерживаемый формат файла: {ext}. Поддерживаемые форматы: {', '.join(self.supported_extensions)}",
                    category=ErrorCategory.DATA_FORMAT,
                    severity=ErrorSeverity.CRITICAL
                )
                self.error_handler.handle_error(error, result)
                return result

            # Читаем данные из файла
            data = self.read_file(file_path)

            # Обрабатываем данные
            result = self.process_data(data)

            logger.info(
                f"Импорт завершен: {result.success_count} записей создано/обновлено, {result.skipped_count} пропущено")

            return result

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                result=result
            )

            logger.error(f"Ошибка при импорте файла {file_path}: {str(e)}")

            return result

    @classmethod
    def import_from_file(cls,
                         file_path: str,
                         model_class: Type[Model],
                         mapping: Optional[Dict[str, str]] = None,
                         **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрого импорта из файла.

        Args:
            file_path: Путь к файлу для импорта.
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            **kwargs: Дополнительные аргументы для конструктора импортера.

        Returns:
            ProcessingResult: Результат импорта.
        """
        importer = cls(model_class=model_class, mapping=mapping, **kwargs)
        return importer.import_file(file_path)
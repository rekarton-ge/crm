"""
Базовый экспортер данных.

Этот модуль содержит абстрактный базовый класс для экспортеров данных,
который определяет общий интерфейс и функциональность для всех экспортеров.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from django.db.models import Model, QuerySet
from django.http import HttpResponse

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


class BaseExporter(ABC):
    """
    Абстрактный базовый класс для всех экспортеров данных.

    Определяет общий интерфейс и функциональность для экспорта данных
    в различные форматы, такие как CSV, Excel и JSON.
    """

    # Название формата экспорта (переопределяется в подклассах)
    format_name = "base"

    # MIME-тип для HTTP-ответа (переопределяется в подклассах)
    content_type = "application/octet-stream"

    # Расширение файла (переопределяется в подклассах)
    file_extension = ""

    def __init__(self,
                 fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None,
                 field_labels: Optional[Dict[str, str]] = None,
                 file_name: Optional[str] = None,
                 error_handler: Optional[ErrorHandler] = None):
        """
        Инициализирует экспортер с указанными настройками.

        Args:
            fields: Список полей для экспорта. Если None, экспортируются все поля.
            exclude_fields: Список полей для исключения из экспорта.
            field_labels: Словарь соответствия имен полей и их отображаемых названий.
            file_name: Имя выходного файла без расширения.
            error_handler: Обработчик ошибок для использования.
        """
        self.fields = fields
        self.exclude_fields = exclude_fields or []
        self.field_labels = field_labels or {}
        self.file_name = file_name
        self.error_handler = error_handler or ErrorHandlerFactory.create_default_handler()

        # Хранит информацию о полях для экспорта
        self.export_fields: List[Dict[str, Any]] = []

    def get_fields(self, queryset: Union[QuerySet, List[Model]]) -> List[Dict[str, Any]]:
        """
        Получает информацию о полях для экспорта из модели или списка моделей.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            List[Dict[str, Any]]: Список словарей с информацией о полях
        """
        if not queryset:
            return []

        # Получаем первый объект для анализа полей
        if isinstance(queryset, QuerySet):
            model = queryset.model
            model_fields = model._meta.fields
        else:
            model = queryset[0].__class__
            model_fields = model._meta.fields

        # Формируем список полей для экспорта
        export_fields = []

        # Если поля явно указаны, используем только их
        if self.fields:
            for field_name in self.fields:
                # Проверяем, что поле существует в модели
                try:
                    model_field = model._meta.get_field(field_name)
                    export_fields.append({
                        'name': field_name,
                        'verbose_name': self.field_labels.get(field_name, model_field.verbose_name),
                        'field': model_field
                    })
                except Exception as e:
                    # Если поле не найдено в модели, но все равно требуется для экспорта
                    export_fields.append({
                        'name': field_name,
                        'verbose_name': self.field_labels.get(field_name, field_name),
                        'field': None
                    })
        else:
            # Иначе используем все поля модели, кроме исключенных
            for field in model_fields:
                if field.name not in self.exclude_fields and not field.primary_key:
                    export_fields.append({
                        'name': field.name,
                        'verbose_name': self.field_labels.get(field.name, field.verbose_name),
                        'field': field
                    })

        return export_fields

    def get_header_row(self) -> List[str]:
        """
        Получает список заголовков для экспорта.

        Returns:
            List[str]: Список заголовков
        """
        return [field['verbose_name'] for field in self.export_fields]

    def get_value(self, obj: Any, field_name: str) -> Any:
        """
        Получает значение поля объекта для экспорта.

        Args:
            obj: Объект для получения значения
            field_name: Имя поля

        Returns:
            Any: Значение поля
        """
        try:
            # Сначала проверяем, есть ли метод get_FIELD_display для полей с choices
            display_method = getattr(obj, f'get_{field_name}_display', None)
            if display_method and callable(display_method):
                return display_method()

            # Затем проверяем, есть ли метод для экспорта поля
            export_method = getattr(obj, f'export_{field_name}', None)
            if export_method and callable(export_method):
                return export_method()

            # Иначе пытаемся получить значение напрямую
            value = getattr(obj, field_name, None)

            # Если значение - функция, вызываем ее
            if callable(value):
                return value()

            return value
        except Exception as e:
            logger.error(f"Ошибка при получении значения поля {field_name}: {str(e)}")
            return None

    def get_row(self, obj: Any) -> List[Any]:
        """
        Получает список значений объекта для экспорта.

        Args:
            obj: Объект для экспорта

        Returns:
            List[Any]: Список значений полей объекта
        """
        return [self.get_value(obj, field['name']) for field in self.export_fields]

    def prepare_data(self, queryset: Union[QuerySet, List[Model]]) -> Tuple[List[str], List[List[Any]]]:
        """
        Подготавливает данные для экспорта.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            Tuple[List[str], List[List[Any]]]: Кортеж из списка заголовков и списка строк данных
        """
        # Получаем информацию о полях для экспорта
        self.export_fields = self.get_fields(queryset)

        # Получаем заголовки
        headers = self.get_header_row()

        # Получаем данные
        data = [self.get_row(obj) for obj in queryset]

        return headers, data

    @abstractmethod
    def export_data(self, queryset: Union[QuerySet, List[Model]]) -> bytes:
        """
        Экспортирует данные в выбранный формат.

        Этот метод должен быть реализован в подклассах.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            bytes: Байтовое представление экспортированных данных
        """
        pass

    def export_to_response(self, queryset: Union[QuerySet, List[Model]],
                           file_name: Optional[str] = None) -> HttpResponse:
        """
        Экспортирует данные в HTTP-ответ для скачивания.

        Args:
            queryset: QuerySet или список моделей для экспорта
            file_name: Имя файла для скачивания

        Returns:
            HttpResponse: HTTP-ответ с экспортированными данными
        """
        # Экспортируем данные
        data = self.export_data(queryset)

        # Создаем HTTP-ответ
        response = HttpResponse(data, content_type=self.content_type)

        # Определяем имя файла
        file_name = file_name or self.file_name or 'export'
        file_name = f"{file_name}.{self.file_extension}"

        # Устанавливаем заголовок для скачивания файла
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return response

    def export_to_file(self, queryset: Union[QuerySet, List[Model]],
                       file_path: Optional[str] = None) -> ProcessingResult:
        """
        Экспортирует данные в файл.

        Args:
            queryset: QuerySet или список моделей для экспорта
            file_path: Путь к файлу для сохранения. Если None, используется имя файла + расширение.

        Returns:
            ProcessingResult: Результат экспорта
        """
        result = ProcessingResult()

        try:
            # Экспортируем данные
            data = self.export_data(queryset)

            # Определяем путь к файлу
            if not file_path:
                file_name = self.file_name or 'export'
                file_path = f"{file_name}.{self.file_extension}"

            # Создаем директорию для файла, если она не существует
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Записываем данные в файл
            with open(file_path, 'wb') as f:
                f.write(data)

            # Обновляем результат
            result.success = True
            result.processed_count = len(queryset) if hasattr(queryset, '__len__') else queryset.count()
            result.success_count = result.processed_count

            logger.info(f"Успешно экспортировано {result.processed_count} записей в {file_path}")

        except Exception as e:
            # Обрабатываем ошибку
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                context={'file_path': file_path},
                result=result
            )

            logger.error(f"Ошибка при экспорте данных в файл {file_path}: {str(e)}")

        return result
"""
JSON экспортер данных.

Этот модуль содержит класс для экспорта данных в формате JSON.
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, QuerySet

from core.data_processing.exporters.base import BaseExporter
from core.data_processing.error_handlers import ErrorHandler

# Настройка логгера
logger = logging.getLogger(__name__)


class CustomJSONEncoder(DjangoJSONEncoder):
    """
    Расширенный JSON-энкодер для поддержки дополнительных типов данных.

    Добавляет поддержку таких типов, как Decimal, datetime и т.д.
    """

    def default(self, obj):
        """
        Преобразует объект в JSON-совместимый формат.

        Args:
            obj: Объект для преобразования

        Returns:
            Преобразованный объект
        """
        # Обработка Decimal
        if isinstance(obj, Decimal):
            return float(obj)

        # Обработка моделей Django
        if isinstance(obj, Model):
            return str(obj)

        # Для остальных типов используем базовый класс
        return super().default(obj)


class JSONExporter(BaseExporter):
    """
    Экспортер данных в формат JSON.

    Экспортирует данные из QuerySet или списка моделей в файл JSON
    с возможностью настройки формата и структуры.
    """

    format_name = "json"
    content_type = "application/json"
    file_extension = "json"

    def __init__(self,
                 fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None,
                 field_labels: Optional[Dict[str, str]] = None,
                 file_name: Optional[str] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 indent: Optional[int] = 4,
                 ensure_ascii: bool = False,
                 use_natural_keys: bool = False,
                 format_values: Optional[Dict[str, callable]] = None,
                 flat_structure: bool = False,
                 root_label: str = "items",
                 include_metadata: bool = False):
        """
        Инициализирует JSON экспортер с указанными настройками.

        Args:
            fields: Список полей для экспорта. Если None, экспортируются все поля.
            exclude_fields: Список полей для исключения из экспорта.
            field_labels: Словарь соответствия имен полей и их отображаемых названий.
            file_name: Имя выходного файла без расширения.
            error_handler: Обработчик ошибок для использования.
            indent: Отступ для форматирования JSON.
            ensure_ascii: Экранировать ли символы не ASCII в результате.
            use_natural_keys: Использовать ли natural keys для связанных объектов.
            format_values: Словарь функций для форматирования значений полей.
            flat_structure: Если True, экспортирует плоский список объектов. Если False,
                           включает структуру с метаданными.
            root_label: Имя корневого элемента для списка объектов.
            include_metadata: Включать ли метаданные о модели и экспорте.
        """
        super().__init__(fields, exclude_fields, field_labels, file_name, error_handler)

        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.use_natural_keys = use_natural_keys
        self.format_values = format_values or {}
        self.flat_structure = flat_structure
        self.root_label = root_label
        self.include_metadata = include_metadata

    def format_value(self, value: Any, field_name: str) -> Any:
        """
        Форматирует значение поля для экспорта в JSON.

        Args:
            value: Значение поля
            field_name: Имя поля

        Returns:
            Any: Отформатированное значение поля
        """
        # Если есть функция форматирования для данного поля, применяем ее
        if field_name in self.format_values and callable(self.format_values[field_name]):
            return self.format_values[field_name](value)

        # Обработка связанных объектов
        if isinstance(value, Model):
            if self.use_natural_keys and hasattr(value, 'natural_key'):
                return value.natural_key()
            else:
                return str(value)

        # Обработка QuerySet
        if isinstance(value, QuerySet):
            return [str(obj) for obj in value]

        # Обработка дат и времени
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        # Обработка Decimal
        if isinstance(value, Decimal):
            return float(value)

        return value

    def get_object_dict(self, obj: Model) -> Dict[str, Any]:
        """
        Преобразует объект в словарь для экспорта.

        Args:
            obj: Объект для экспорта

        Returns:
            Dict[str, Any]: Словарь с данными объекта
        """
        result = {}

        for field in self.export_fields:
            field_name = field['name']
            value = self.get_value(obj, field_name)
            result[field_name] = self.format_value(value, field_name)

        return result

    def prepare_json_data(self, queryset: Union[QuerySet, List[Model]]) -> Dict[str, Any]:
        """
        Подготавливает данные для экспорта в JSON.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            Dict[str, Any]: Словарь с данными для экспорта
        """
        # Получаем информацию о полях для экспорта
        self.export_fields = self.get_fields(queryset)

        # Преобразуем объекты в словари
        objects_data = [self.get_object_dict(obj) for obj in queryset]

        if self.flat_structure:
            # Возвращаем только список объектов
            return objects_data
        else:
            # Создаем структуру с корневым элементом
            result = {
                self.root_label: objects_data
            }

            # Добавляем метаданные, если нужно
            if self.include_metadata:
                # Определяем модель
                model = queryset.model if isinstance(queryset, QuerySet) else queryset[0].__class__

                result['metadata'] = {
                    'model': f"{model._meta.app_label}.{model._meta.model_name}",
                    'count': len(objects_data),
                    'fields': [field['name'] for field in self.export_fields],
                    'export_date': datetime.now().isoformat()
                }

            return result

    def export_data(self, queryset: Union[QuerySet, List[Model]]) -> bytes:
        """
        Экспортирует данные в формат JSON.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            bytes: Байтовое представление JSON-файла
        """
        # Подготовка данных для экспорта
        json_data = self.prepare_json_data(queryset)

        # Сериализуем данные в JSON
        json_string = json.dumps(
            json_data,
            cls=CustomJSONEncoder,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii
        )

        # Возвращаем данные как байты в UTF-8
        return json_string.encode('utf-8')

    @classmethod
    def export_queryset(cls,
                        queryset: Union[QuerySet, List[Model]],
                        fields: Optional[List[str]] = None,
                        file_name: Optional[str] = None,
                        **kwargs) -> bytes:
        """
        Статический метод для быстрого экспорта QuerySet в JSON.

        Args:
            queryset: QuerySet или список моделей для экспорта
            fields: Список полей для экспорта
            file_name: Имя выходного файла
            **kwargs: Дополнительные аргументы для конструктора JSONExporter

        Returns:
            bytes: Байтовое представление JSON-файла
        """
        exporter = cls(fields=fields, file_name=file_name, **kwargs)
        return exporter.export_data(queryset)
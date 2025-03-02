"""
CSV экспортер данных.

Этот модуль содержит класс для экспорта данных в формате CSV.
"""

import csv
import io
import logging
from typing import Any, Dict, List, Optional, Union

from django.db.models import Model, QuerySet

from core.data_processing.exporters.base import BaseExporter
from core.data_processing.error_handlers import ErrorHandler

# Настройка логгера
logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """
    Экспортер данных в формат CSV.

    Экспортирует данные из QuerySet или списка моделей в файл CSV.
    """

    format_name = "csv"
    content_type = "text/csv"
    file_extension = "csv"

    def __init__(self,
                 fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None,
                 field_labels: Optional[Dict[str, str]] = None,
                 file_name: Optional[str] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 delimiter: str = ',',
                 quotechar: str = '"',
                 encoding: str = 'utf-8',
                 include_headers: bool = True,
                 format_values: Optional[Dict[str, callable]] = None):
        """
        Инициализирует CSV экспортер с указанными настройками.

        Args:
            fields: Список полей для экспорта. Если None, экспортируются все поля.
            exclude_fields: Список полей для исключения из экспорта.
            field_labels: Словарь соответствия имен полей и их отображаемых названий.
            file_name: Имя выходного файла без расширения.
            error_handler: Обработчик ошибок для использования.
            delimiter: Разделитель полей CSV.
            quotechar: Символ кавычек CSV.
            encoding: Кодировка файла.
            include_headers: Включать ли заголовки в CSV.
            format_values: Словарь функций для форматирования значений полей.
        """
        super().__init__(fields, exclude_fields, field_labels, file_name, error_handler)

        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.include_headers = include_headers
        self.format_values = format_values or {}

    def format_value(self, value: Any, field_name: str) -> str:
        """
        Форматирует значение поля для экспорта в CSV.

        Args:
            value: Значение поля
            field_name: Имя поля

        Returns:
            str: Отформатированное значение поля
        """
        # Если есть функция форматирования для данного поля, применяем ее
        if field_name in self.format_values and callable(self.format_values[field_name]):
            return self.format_values[field_name](value)

        # Обработка None
        if value is None:
            return ""

        # Преобразование значения в строку
        return str(value)

    def get_row(self, obj: Any) -> List[str]:
        """
        Получает список значений объекта для экспорта в CSV.

        Args:
            obj: Объект для экспорта

        Returns:
            List[str]: Список значений полей объекта в виде строк
        """
        return [
            self.format_value(self.get_value(obj, field['name']), field['name'])
            for field in self.export_fields
        ]

    def export_data(self, queryset: Union[QuerySet, List[Model]]) -> bytes:
        """
        Экспортирует данные в формат CSV.

        Args:
            queryset: QuerySet или список моделей для экспорта

        Returns:
            bytes: Байтовое представление CSV-файла
        """
        # Подготовка данных для экспорта
        headers, data = self.prepare_data(queryset)

        # Создаем буфер для записи CSV
        csv_buffer = io.StringIO()

        # Создаем CSV writer
        csv_writer = csv.writer(
            csv_buffer,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=csv.QUOTE_MINIMAL
        )

        # Записываем заголовки, если нужно
        if self.include_headers:
            csv_writer.writerow(headers)

        # Записываем данные
        for row in data:
            csv_writer.writerow(row)

        # Возвращаем данные как байты
        return csv_buffer.getvalue().encode(self.encoding)

    @classmethod
    def export_queryset(cls,
                        queryset: Union[QuerySet, List[Model]],
                        fields: Optional[List[str]] = None,
                        file_name: Optional[str] = None,
                        **kwargs) -> bytes:
        """
        Статический метод для быстрого экспорта QuerySet в CSV.

        Args:
            queryset: QuerySet или список моделей для экспорта
            fields: Список полей для экспорта
            file_name: Имя выходного файла
            **kwargs: Дополнительные аргументы для конструктора CSVExporter

        Returns:
            bytes: Байтовое представление CSV-файла
        """
        exporter = cls(fields=fields, file_name=file_name, **kwargs)
        return exporter.export_data(queryset)
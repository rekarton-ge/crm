"""
CSV импортер данных.

Этот модуль содержит класс для импорта данных из CSV-файлов в модели Django.
"""

import csv
import logging
from typing import Any, Dict, List, Optional, Type, Union

from django.db.models import Model

from core.data_processing.error_handlers import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    ProcessingError,
    ProcessingResult
)
from core.data_processing.importers.base import BaseImporter

# Настройка логгера
logger = logging.getLogger(__name__)


class CSVImporter(BaseImporter):
    """
    Импортер данных из CSV-файлов.

    Позволяет импортировать данные из CSV-файлов в модели Django
    с гибкой настройкой параметров импорта.
    """

    format_name = "csv"
    supported_extensions = ["csv", "txt"]

    def __init__(self,
                 model_class: Type[Model],
                 mapping: Optional[Dict[str, str]] = None,
                 delimiter: str = ',',
                 quotechar: str = '"',
                 encoding: str = 'utf-8',
                 has_header: bool = True,
                 detect_header: bool = True,
                 header_row: int = 0,
                 **kwargs):
        """
        Инициализирует CSV импортер с указанными настройками.

        Args:
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            delimiter: Разделитель полей CSV.
            quotechar: Символ кавычек CSV.
            encoding: Кодировка файла.
            has_header: Имеет ли файл строку заголовка.
            detect_header: Пытаться ли автоматически определить заголовки.
            header_row: Номер строки заголовка (если has_header=True).
            **kwargs: Дополнительные аргументы для базового импортера.
        """
        super().__init__(model_class, mapping, **kwargs)

        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.has_header = has_header
        self.detect_header = detect_header
        self.header_row = header_row

        # Для хранения заголовков CSV
        self.headers = []

    def auto_detect_header(self, data: List[List[str]]) -> List[str]:
        """
        Автоматически определяет заголовки CSV из первой строки.

        Args:
            data: Данные CSV в виде списка строк.

        Returns:
            List[str]: Список заголовков.
        """
        if not data:
            return []

        # Берем строку заголовка
        header_row_data = data[self.header_row]

        # Нормализуем заголовки: удаляем лишние пробелы, приводим к нижнему регистру
        headers = [h.strip() for h in header_row_data]

        return headers

    def create_mapping_from_headers(self, headers: List[str]) -> Dict[str, str]:
        """
        Создает отображение полей на основе заголовков CSV.

        Args:
            headers: Список заголовков CSV.

        Returns:
            Dict[str, str]: Словарь отображения полей.
        """
        mapping = {}

        # Получаем список полей модели в нижнем регистре
        model_fields_lower = [field.lower() for field in self.model_fields]

        for i, header in enumerate(headers):
            # Нормализуем заголовок
            normalized_header = header.lower().strip()

            # Проверяем точное совпадение заголовка с полем модели
            if normalized_header in self.model_fields:
                mapping[i] = normalized_header
                continue

            # Проверяем, совпадает ли заголовок с полем модели без учета регистра
            if normalized_header in model_fields_lower:
                idx = model_fields_lower.index(normalized_header)
                mapping[i] = self.model_fields[idx]
                continue

            # Проверяем, содержит ли заголовок имя поля модели
            for field in self.model_fields:
                if field.lower() in normalized_header.lower():
                    mapping[i] = field
                    break

        return mapping

    def read_csv(self, file_path: str) -> List[List[str]]:
        """
        Читает данные из CSV-файла.

        Args:
            file_path: Путь к CSV-файлу.

        Returns:
            List[List[str]]: Список строк из CSV-файла.
        """
        data = []

        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                reader = csv.reader(f, delimiter=self.delimiter, quotechar=self.quotechar)
                data = list(reader)

            return data

        except Exception as e:
            logger.error(f"Ошибка при чтении CSV-файла: {str(e)}")
            raise

    def process_csv_data(self, data: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Обрабатывает данные из CSV и преобразует их в список словарей.

        Args:
            data: Данные CSV в виде списка строк.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными.
        """
        if not data:
            return []

        result = []

        # Определяем заголовки
        if self.has_header:
            if self.header_row >= len(data):
                raise ValueError(
                    f"Номер строки заголовка ({self.header_row}) превышает количество строк в файле ({len(data)})")

            self.headers = self.auto_detect_header(data)

            # Если mapping не задан и нужно определить его автоматически
            if not self.mapping and self.detect_header:
                self.mapping = self.create_mapping_from_headers(self.headers)
                logger.info(f"Автоматически определено отображение полей: {self.mapping}")

            # Удаляем строку заголовка из данных
            data = data[:self.header_row] + data[self.header_row + 1:]

        # Если нет заголовков и не задано отображение
        if not self.headers and not self.mapping:
            # Используем индексы колонок как ключи
            for row_idx, row in enumerate(data):
                row_data = {}
                for col_idx, value in enumerate(row):
                    row_data[col_idx] = value
                result.append(row_data)
        # Если есть заголовки или задано отображение
        else:
            for row_idx, row in enumerate(data):
                row_data = {}

                # Если задано отображение по индексам
                if all(isinstance(k, int) for k in self.mapping.keys()):
                    for col_idx, model_field in self.mapping.items():
                        if col_idx < len(row):
                            row_data[col_idx] = row[col_idx]
                # Если задано отображение по именам полей
                elif self.headers:
                    for col_idx, header in enumerate(self.headers):
                        if col_idx < len(row):
                            row_data[header] = row[col_idx]

                result.append(row_data)

        return result

    def read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Читает данные из CSV-файла и преобразует их в список словарей.

        Args:
            file_path: Путь к CSV-файлу.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными.
        """
        # Читаем CSV-файл
        csv_data = self.read_csv(file_path)

        # Обрабатываем данные CSV
        return self.process_csv_data(csv_data)

    @classmethod
    def import_from_csv(cls,
                        file_path: str,
                        model_class: Type[Model],
                        mapping: Optional[Dict[str, str]] = None,
                        **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрого импорта из CSV-файла.

        Args:
            file_path: Путь к CSV-файлу.
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            **kwargs: Дополнительные аргументы для конструктора CSVImporter.

        Returns:
            ProcessingResult: Результат импорта.
        """
        importer = cls(model_class=model_class, mapping=mapping, **kwargs)
        return importer.import_file(file_path)
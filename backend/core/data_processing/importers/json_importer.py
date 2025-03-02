"""
JSON импортер данных.

Этот модуль содержит класс для импорта данных из JSON-файлов в модели Django.
"""

import json
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


class JSONImporter(BaseImporter):
    """
    Импортер данных из JSON-файлов.

    Позволяет импортировать данные из JSON-файлов в модели Django
    с поддержкой различных структур JSON.
    """

    format_name = "json"
    supported_extensions = ["json"]

    def __init__(self,
                 model_class: Type[Model],
                 mapping: Optional[Dict[str, str]] = None,
                 root_element: Optional[str] = None,
                 flatten_nested: bool = False,
                 handle_arrays: bool = True,
                 encoding: str = 'utf-8',
                 **kwargs):
        """
        Инициализирует JSON импортер с указанными настройками.

        Args:
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            root_element: Имя корневого элемента в JSON, содержащего данные.
            flatten_nested: Объединять ли вложенные объекты в плоскую структуру.
            handle_arrays: Обрабатывать ли массивы как отдельные объекты.
            encoding: Кодировка файла.
            **kwargs: Дополнительные аргументы для базового импортера.
        """
        super().__init__(model_class, mapping, **kwargs)

        self.root_element = root_element
        self.flatten_nested = flatten_nested
        self.handle_arrays = handle_arrays
        self.encoding = encoding

    def flatten_object(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Преобразует вложенный объект в плоскую структуру.

        Args:
            data: Словарь с вложенными объектами.
            prefix: Префикс для ключей (используется при рекурсивном вызове).

        Returns:
            Dict[str, Any]: Словарь с плоской структурой.
        """
        result = {}

        for key, value in data.items():
            new_key = f"{prefix}{key}" if prefix else key

            # Если значение - словарь, рекурсивно обрабатываем его
            if isinstance(value, dict):
                nested_result = self.flatten_object(value, f"{new_key}_")
                result.update(nested_result)
            # Если значение - список и нужно обрабатывать массивы
            elif isinstance(value, list) and self.handle_arrays:
                # Для списков создаем строковое представление
                result[new_key] = json.dumps(value)
            else:
                result[new_key] = value

        return result

    def read_json(self, file_path: str) -> Any:
        """
        Читает данные из JSON-файла.

        Args:
            file_path: Путь к JSON-файлу.

        Returns:
            Any: Данные из JSON-файла.
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                return json.load(f)

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при декодировании JSON: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Ошибка при чтении JSON-файла: {str(e)}")
            raise

    def process_json_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Обрабатывает данные из JSON и преобразует их в список словарей.

        Args:
            data: Данные из JSON-файла.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными.
        """
        result = []

        # Если указан корневой элемент, извлекаем данные из него
        if self.root_element:
            if isinstance(data, dict) and self.root_element in data:
                data = data[self.root_element]
            else:
                logger.warning(f"Корневой элемент '{self.root_element}' не найден в JSON")

        # Если данные - список объектов
        if isinstance(data, list):
            for item in data:
                # Пропускаем элементы, которые не являются словарями
                if not isinstance(item, dict):
                    continue

                # Если нужно обрабатывать вложенные объекты
                if self.flatten_nested:
                    item = self.flatten_object(item)

                result.append(item)
        # Если данные - словарь
        elif isinstance(data, dict):
            # Если нужно обрабатывать вложенные объекты
            if self.flatten_nested:
                data = self.flatten_object(data)

            result.append(data)
        else:
            logger.warning(f"Неподдерживаемый формат данных JSON: {type(data)}")

        return result

    def read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Читает данные из JSON-файла и преобразует их в список словарей.

        Args:
            file_path: Путь к JSON-файлу.

        Returns:
            List[Dict[str, Any]]: Список словарей с данными.
        """
        # Читаем JSON-файл
        json_data = self.read_json(file_path)

        # Обрабатываем данные JSON
        return self.process_json_data(json_data)

    @classmethod
    def import_from_json(cls,
                         file_path: str,
                         model_class: Type[Model],
                         mapping: Optional[Dict[str, str]] = None,
                         **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрого импорта из JSON-файла.

        Args:
            file_path: Путь к JSON-файлу.
            model_class: Класс модели Django для импорта данных.
            mapping: Словарь соответствия полей в файле полям модели.
            **kwargs: Дополнительные аргументы для конструктора JSONImporter.

        Returns:
            ProcessingResult: Результат импорта.
        """
        importer = cls(model_class=model_class, mapping=mapping, **kwargs)
        return importer.import_file(file_path)
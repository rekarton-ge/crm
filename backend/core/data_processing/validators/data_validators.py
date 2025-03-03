"""
Валидаторы данных для импорта и обработки.

Этот модуль содержит классы валидаторов данных для проверки и валидации
различных типов данных (текст, числа, даты, email и т.д.).
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, Callable

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, QuerySet

from core.data_processing.validators.base_validator import (
    BaseValidator,
    ValidationError,
    ValidationResult
)

# Настройка логгера
logger = logging.getLogger(__name__)


class DataValidator(BaseValidator):
    """
    Базовый класс для валидаторов данных.

    Предоставляет общую логику для всех валидаторов данных,
    включая поддержку обязательности полей и пользовательских сообщений.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 **kwargs):
        """
        Инициализирует валидатор данных.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(**kwargs)
        self.field_name = field_name
        self.required = required
        self.error_message = error_message

    def validate(self, data: Any) -> ValidationResult:
        """
        Валидирует данные.

        Args:
            data: Данные для валидации.

        Returns:
            ValidationResult: Результат валидации.
        """
        result = ValidationResult()

        # Проверка на обязательность
        if self.required and (data is None or data == ""):
            message = self.error_message or f"Поле '{self.field_name}' обязательно для заполнения."
            result.add_error(message, field_name=self.field_name)
            return result

        # Если поле не обязательное и данные пусты, считаем это валидным
        if not self.required and (data is None or data == ""):
            return result

        # Выполняем конкретную валидацию
        return self._validate(data, result)

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Выполняет конкретную валидацию данных.

        Этот метод должен быть переопределен в подклассах.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        return result


class DataFormatValidator(DataValidator):
    """
    Валидатор формата данных на основе регулярных выражений.

    Проверяет соответствие данных указанному регулярному выражению.
    """

    def __init__(self,
                 pattern: Union[str, Pattern],
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 match_message: Optional[str] = None,
                 **kwargs):
        """
        Инициализирует валидатор формата данных.

        Args:
            pattern: Регулярное выражение для проверки.
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            match_message: Пользовательское сообщение об ошибке при несоответствии формату.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern

        self.match_message = match_message

    def _validate(self, data: str, result: ValidationResult) -> ValidationResult:
        """
        Проверяет соответствие данных регулярному выражению.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        # Преобразуем данные в строку
        data_str = str(data) if data is not None else ""

        # Проверяем на соответствие шаблону
        if not self.pattern.match(data_str):
            field_name = self.field_name or "Поле"
            message = self.match_message or f"{field_name} не соответствует требуемому формату."
            result.add_error(message, field_name=self.field_name)

        return result


class NumericValidator(DataValidator):
    """
    Валидатор числовых данных.

    Проверяет, что данные являются числом, и опционально проверяет
    минимальное и максимальное значения, целочисленность и другие параметры.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None,
                 integer_only: bool = False,
                 positive_only: bool = False,
                 negative_only: bool = False,
                 **kwargs):
        """
        Инициализирует валидатор числовых данных.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            min_value: Минимальное допустимое значение.
            max_value: Максимальное допустимое значение.
            integer_only: Разрешены только целые числа.
            positive_only: Разрешены только положительные числа.
            negative_only: Разрешены только отрицательные числа.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
        self.positive_only = positive_only
        self.negative_only = negative_only

        # Проверяем, что параметры не конфликтуют
        if positive_only and negative_only:
            raise ValueError("Параметры positive_only и negative_only не могут быть одновременно True")

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет числовые данные.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Поле"

        # Пробуем преобразовать в число
        try:
            if isinstance(data, str):
                # Заменяем запятую на точку для корректного парсинга
                data = data.replace(',', '.')

            if self.integer_only:
                # Для целых чисел используем int
                value = int(float(data))

                # Проверяем, что число действительно целое
                if float(data) != value:
                    result.add_error(f"{field_name} должно быть целым числом.", field_name=self.field_name)
                    return result
            else:
                # Для других чисел используем float
                value = float(data)
        except (ValueError, TypeError):
            result.add_error(f"{field_name} должно быть числом.", field_name=self.field_name)
            return result

        # Проверка на положительное/отрицательное
        if self.positive_only and value <= 0:
            result.add_error(f"{field_name} должно быть положительным числом.", field_name=self.field_name)

        if self.negative_only and value >= 0:
            result.add_error(f"{field_name} должно быть отрицательным числом.", field_name=self.field_name)

        # Проверка на минимальное значение
        if self.min_value is not None and value < self.min_value:
            result.add_error(f"{field_name} должно быть не меньше {self.min_value}.", field_name=self.field_name)

        # Проверка на максимальное значение
        if self.max_value is not None and value > self.max_value:
            result.add_error(f"{field_name} должно быть не больше {self.max_value}.", field_name=self.field_name)

        return result


class StringValidator(DataValidator):
    """
    Валидатор строковых данных.

    Проверяет длину строки, опциональную проверку на включение/исключение
    определенных подстрок и другие параметры.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 contains: Optional[List[str]] = None,
                 not_contains: Optional[List[str]] = None,
                 choices: Optional[List[str]] = None,
                 strip: bool = True,
                 **kwargs):
        """
        Инициализирует валидатор строковых данных.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            min_length: Минимальная длина строки.
            max_length: Максимальная длина строки.
            contains: Список подстрок, которые должны содержаться в строке.
            not_contains: Список подстрок, которые не должны содержаться в строке.
            choices: Список допустимых значений.
            strip: Удалять ли пробельные символы в начале и конце строки.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        self.min_length = min_length
        self.max_length = max_length
        self.contains = contains or []
        self.not_contains = not_contains or []
        self.choices = choices
        self.strip = strip

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет строковые данные.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Поле"

        # Преобразуем данные в строку
        if data is None:
            data_str = ""
        else:
            data_str = str(data)

        # Удаляем пробельные символы, если нужно
        if self.strip:
            data_str = data_str.strip()

        # Проверка длины
        if self.min_length is not None and len(data_str) < self.min_length:
            result.add_error(f"{field_name} должно содержать не менее {self.min_length} символов.",
                             field_name=self.field_name)

        if self.max_length is not None and len(data_str) > self.max_length:
            result.add_error(f"{field_name} должно содержать не более {self.max_length} символов.",
                             field_name=self.field_name)

        # Проверка на вхождение подстрок
        for substring in self.contains:
            if substring not in data_str:
                result.add_error(f"{field_name} должно содержать '{substring}'.", field_name=self.field_name)

        # Проверка на отсутствие запрещенных подстрок
        for substring in self.not_contains:
            if substring in data_str:
                result.add_error(f"{field_name} не должно содержать '{substring}'.", field_name=self.field_name)

        # Проверка на допустимые значения
        if self.choices is not None and data_str not in self.choices:
            choices_str = ", ".join([f"'{choice}'" for choice in self.choices])
            result.add_error(f"{field_name} должно быть одним из следующих значений: {choices_str}.",
                             field_name=self.field_name)

        return result


class DateValidator(DataValidator):
    """
    Валидатор данных даты и времени.

    Проверяет формат даты, минимальное и максимальное значения.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 format: str = "%Y-%m-%d",
                 min_date: Optional[Union[str, datetime]] = None,
                 max_date: Optional[Union[str, datetime]] = None,
                 **kwargs):
        """
        Инициализирует валидатор данных даты.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            format: Формат даты для парсинга строк.
            min_date: Минимальная допустимая дата.
            max_date: Максимальная допустимая дата.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        self.format = format

        # Преобразуем min_date в datetime, если это строка
        if isinstance(min_date, str):
            try:
                self.min_date = datetime.strptime(min_date, self.format)
            except ValueError:
                raise ValueError(f"Неверный формат min_date. Ожидается формат {self.format}")
        else:
            self.min_date = min_date

        # Преобразуем max_date в datetime, если это строка
        if isinstance(max_date, str):
            try:
                self.max_date = datetime.strptime(max_date, self.format)
            except ValueError:
                raise ValueError(f"Неверный формат max_date. Ожидается формат {self.format}")
        else:
            self.max_date = max_date

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет данные даты.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Поле"

        # Если уже datetime, используем как есть
        if isinstance(data, datetime):
            date_value = data
        else:
            # Пробуем преобразовать строку в datetime
            try:
                data_str = str(data).strip() if data is not None else ""
                date_value = datetime.strptime(data_str, self.format)
            except ValueError:
                result.add_error(f"{field_name} должно быть датой в формате {self.format}.", field_name=self.field_name)
                return result

        # Проверка на минимальную дату
        if self.min_date is not None and date_value < self.min_date:
            min_date_str = self.min_date.strftime(self.format)
            result.add_error(f"{field_name} должно быть не раньше {min_date_str}.", field_name=self.field_name)

        # Проверка на максимальную дату
        if self.max_date is not None and date_value > self.max_date:
            max_date_str = self.max_date.strftime(self.format)
            result.add_error(f"{field_name} должно быть не позже {max_date_str}.", field_name=self.field_name)

        return result


class EmailValidator(DataValidator):
    """
    Валидатор email-адресов.

    Проверяет корректность формата email-адреса.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 allowed_domains: Optional[List[str]] = None,
                 **kwargs):
        """
        Инициализирует валидатор email-адресов.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            allowed_domains: Список разрешенных доменов.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        self.allowed_domains = allowed_domains

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет email-адрес.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Email"

        # Преобразуем данные в строку
        data_str = str(data).strip() if data is not None else ""

        # Проверяем формат email
        try:
            validate_email(data_str)
        except DjangoValidationError:
            result.add_error(f"{field_name} должен быть корректным email-адресом.", field_name=self.field_name)
            return result

        # Проверяем домен, если указаны разрешенные домены
        if self.allowed_domains:
            domain = data_str.split('@')[-1].lower()
            if domain not in self.allowed_domains:
                domains_str = ", ".join(self.allowed_domains)
                result.add_error(f"{field_name} должен принадлежать одному из доменов: {domains_str}.",
                                 field_name=self.field_name)

        return result


class PhoneValidator(DataValidator):
    """
    Валидатор телефонных номеров.

    Проверяет корректность формата телефонного номера.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 required: bool = False,
                 error_message: Optional[str] = None,
                 pattern: Optional[Union[str, Pattern]] = None,
                 normalize: bool = True,
                 **kwargs):
        """
        Инициализирует валидатор телефонных номеров.

        Args:
            field_name: Имя поля, которое валидируется.
            required: Является ли поле обязательным.
            error_message: Пользовательское сообщение об ошибке при отсутствии данных.
            pattern: Регулярное выражение для проверки формата номера.
            normalize: Нормализовать ли номер перед проверкой (удалить пробелы, скобки, дефисы).
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=required, error_message=error_message, **kwargs)

        # Используем стандартный шаблон, если не указан собственный
        if pattern is None:
            # Шаблон для российских номеров в формате +7XXXXXXXXXX
            pattern = r'^\+?7[0-9]{10}$'

        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern

        self.normalize = normalize

    def _normalize_phone(self, phone: str) -> str:
        """
        Нормализует телефонный номер, удаляя пробелы, скобки и дефисы.

        Args:
            phone: Телефонный номер для нормализации.

        Returns:
            str: Нормализованный телефонный номер.
        """
        if not phone:
            return ""

        # Удаляем все символы, кроме цифр и знака +
        return re.sub(r'[^0-9+]', '', phone)

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет телефонный номер.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Телефон"

        # Преобразуем данные в строку
        data_str = str(data).strip() if data is not None else ""

        # Нормализуем номер, если требуется
        if self.normalize:
            data_str = self._normalize_phone(data_str)

        # Проверяем формат номера
        if not self.pattern.match(data_str):
            result.add_error(f"{field_name} должен быть корректным телефонным номером.", field_name=self.field_name)

        return result


class RequiredFieldValidator(DataValidator):
    """
    Валидатор обязательных полей.

    Проверяет, что значение поля не пустое.
    """

    def __init__(self,
                 field_name: Optional[str] = None,
                 error_message: Optional[str] = None,
                 **kwargs):
        """
        Инициализирует валидатор обязательных полей.

        Args:
            field_name: Имя поля, которое валидируется.
            error_message: Пользовательское сообщение об ошибке.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, required=True, error_message=error_message, **kwargs)

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет, что значение поля не пустое.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        # Базовая проверка на обязательность уже выполнена в методе validate родительского класса
        return result


class UniqueValidator(DataValidator):
    """
    Валидатор уникальности значений.

    Проверяет, что значение поля уникально в указанной модели.
    """

    def __init__(self,
                 model_class: Type[Model],
                 field_name: str,
                 case_insensitive: bool = False,
                 exclude_id: Optional[int] = None,
                 error_message: Optional[str] = None,
                 **kwargs):
        """
        Инициализирует валидатор уникальности.

        Args:
            model_class: Класс модели для проверки уникальности.
            field_name: Имя поля, которое валидируется (в модели).
            case_insensitive: Игнорировать ли регистр при проверке (для строк).
            exclude_id: ID объекта, который следует исключить из проверки.
            error_message: Пользовательское сообщение об ошибке.
            **kwargs: Дополнительные аргументы для базового валидатора.
        """
        super().__init__(field_name=field_name, error_message=error_message, **kwargs)

        self.model_class = model_class
        self.case_insensitive = case_insensitive
        self.exclude_id = exclude_id

    def _validate(self, data: Any, result: ValidationResult) -> ValidationResult:
        """
        Проверяет уникальность значения в модели.

        Args:
            data: Данные для валидации.
            result: Результат валидации для обновления.

        Returns:
            ValidationResult: Обновленный результат валидации.
        """
        field_name = self.field_name or "Поле"

        # Строим запрос для проверки уникальности
        if self.case_insensitive and isinstance(data, str):
            # Для строк с игнорированием регистра
            query = {f"{self.field_name}__iexact": data}
        else:
            query = {self.field_name: data}

        # Создаем запрос к модели
        qs = self.model_class.objects.filter(**query)

        # Исключаем текущий объект, если указан ID
        if self.exclude_id is not None:
            qs = qs.exclude(pk=self.exclude_id)

        # Проверяем, существует ли объект с таким значением
        if qs.exists():
            error_message = self.error_message or f"{field_name} со значением '{data}' уже существует."
            result.add_error(error_message, field_name=self.field_name)

        return result
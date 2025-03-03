"""
Валидаторы для текста.

Этот модуль содержит валидаторы для текстовых полей.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class RegexValidator:
    """
    Валидатор для проверки соответствия регулярному выражению.
    
    Проверяет, что значение соответствует регулярному выражению.
    """
    
    def __init__(
        self,
        regex: Union[str, Pattern],
        message: Optional[str] = None,
        inverse_match: bool = False
    ):
        """
        Инициализация валидатора.
        
        Args:
            regex (Union[str, Pattern]): Регулярное выражение.
            message (str, optional): Сообщение об ошибке.
            inverse_match (bool, optional): Инвертировать результат проверки.
        """
        self.regex = regex if isinstance(regex, Pattern) else re.compile(regex)
        self.message = message or _(
            'Значение "%(value)s" не соответствует формату.'
        )
        self.inverse_match = inverse_match
    
    def __call__(self, value: str) -> None:
        """
        Проверяет соответствие значения регулярному выражению.
        
        Args:
            value (str): Проверяемое значение.
        
        Raises:
            ValidationError: Если значение не соответствует регулярному выражению.
        """
        match = bool(self.regex.match(value))
        
        if self.inverse_match:
            match = not match
        
        if not match:
            raise ValidationError(
                self.message,
                params={'value': value}
            )


@deconstructible
class ProhibitedWordsValidator:
    """
    Валидатор для проверки отсутствия запрещенных слов.
    
    Проверяет, что значение не содержит запрещенных слов.
    """
    
    def __init__(
        self,
        prohibited_words: List[str],
        message: Optional[str] = None,
        case_sensitive: bool = False
    ):
        """
        Инициализация валидатора.
        
        Args:
            prohibited_words (List[str]): Список запрещенных слов.
            message (str, optional): Сообщение об ошибке.
            case_sensitive (bool, optional): Учитывать регистр.
        """
        self.prohibited_words = prohibited_words
        self.message = message or _(
            'Значение содержит запрещенные слова: %(words)s.'
        )
        self.case_sensitive = case_sensitive
    
    def __call__(self, value: str) -> None:
        """
        Проверяет отсутствие запрещенных слов в значении.
        
        Args:
            value (str): Проверяемое значение.
        
        Raises:
            ValidationError: Если значение содержит запрещенные слова.
        """
        if not self.case_sensitive:
            value = value.lower()
            prohibited_words = [word.lower() for word in self.prohibited_words]
        else:
            prohibited_words = self.prohibited_words
        
        found_words = []
        
        for word in prohibited_words:
            if word in value:
                found_words.append(word)
        
        if found_words:
            raise ValidationError(
                self.message,
                params={'words': ', '.join(found_words), 'value': value}
            )


@deconstructible
class MinWordsValidator:
    """
    Валидатор для проверки минимального количества слов.
    
    Проверяет, что значение содержит не менее указанного количества слов.
    """
    
    def __init__(self, min_words: int, message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            min_words (int): Минимальное количество слов.
            message (str, optional): Сообщение об ошибке.
        """
        self.min_words = min_words
        self.message = message or _(
            'Значение должно содержать не менее %(min_words)d слов.'
        )
    
    def __call__(self, value: str) -> None:
        """
        Проверяет минимальное количество слов в значении.
        
        Args:
            value (str): Проверяемое значение.
        
        Raises:
            ValidationError: Если значение содержит меньше слов, чем требуется.
        """
        words = value.split()
        
        if len(words) < self.min_words:
            raise ValidationError(
                self.message,
                params={'min_words': self.min_words, 'value': value}
            )


@deconstructible
class MaxWordsValidator:
    """
    Валидатор для проверки максимального количества слов.
    
    Проверяет, что значение содержит не более указанного количества слов.
    """
    
    def __init__(self, max_words: int, message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            max_words (int): Максимальное количество слов.
            message (str, optional): Сообщение об ошибке.
        """
        self.max_words = max_words
        self.message = message or _(
            'Значение должно содержать не более %(max_words)d слов.'
        )
    
    def __call__(self, value: str) -> None:
        """
        Проверяет максимальное количество слов в значении.
        
        Args:
            value (str): Проверяемое значение.
        
        Raises:
            ValidationError: Если значение содержит больше слов, чем разрешено.
        """
        words = value.split()
        
        if len(words) > self.max_words:
            raise ValidationError(
                self.message,
                params={'max_words': self.max_words, 'value': value}
            )


@deconstructible
class HTMLValidator:
    """
    Валидатор для проверки HTML-кода.
    
    Проверяет, что HTML-код соответствует требованиям.
    """
    
    def __init__(
        self,
        allowed_tags: Optional[List[str]] = None,
        allowed_attributes: Optional[Dict[str, List[str]]] = None,
        message: Optional[str] = None
    ):
        """
        Инициализация валидатора.
        
        Args:
            allowed_tags (List[str], optional): Список разрешенных тегов.
            allowed_attributes (Dict[str, List[str]], optional): Словарь разрешенных атрибутов для тегов.
            message (str, optional): Сообщение об ошибке.
        """
        self.allowed_tags = allowed_tags or []
        self.allowed_attributes = allowed_attributes or {}
        self.message = message or _(
            'HTML-код содержит запрещенные теги или атрибуты.'
        )
    
    def __call__(self, value: str) -> None:
        """
        Проверяет HTML-код.
        
        Args:
            value (str): Проверяемый HTML-код.
        
        Raises:
            ValidationError: Если HTML-код содержит запрещенные теги или атрибуты.
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(value, 'html.parser')
        
        # Проверяем теги
        if self.allowed_tags:
            for tag in soup.find_all():
                if tag.name not in self.allowed_tags:
                    raise ValidationError(
                        _('HTML-код содержит запрещенный тег: %(tag)s.'),
                        params={'tag': tag.name, 'value': value}
                    )
        
        # Проверяем атрибуты
        if self.allowed_attributes:
            for tag in soup.find_all():
                tag_name = tag.name
                
                for attr in tag.attrs:
                    if tag_name in self.allowed_attributes:
                        if attr not in self.allowed_attributes[tag_name]:
                            raise ValidationError(
                                _('Тег %(tag)s содержит запрещенный атрибут: %(attr)s.'),
                                params={'tag': tag_name, 'attr': attr, 'value': value}
                            )
                    else:
                        raise ValidationError(
                            _('Для тега %(tag)s не определены разрешенные атрибуты.'),
                            params={'tag': tag_name, 'value': value}
                        )


@deconstructible
class URLValidator:
    """
    Валидатор для проверки URL.
    
    Проверяет, что значение является корректным URL.
    """
    
    def __init__(
        self,
        schemes: Optional[List[str]] = None,
        message: Optional[str] = None
    ):
        """
        Инициализация валидатора.
        
        Args:
            schemes (List[str], optional): Список разрешенных схем URL.
            message (str, optional): Сообщение об ошибке.
        """
        self.schemes = schemes or ['http', 'https']
        self.message = message or _(
            'Значение "%(value)s" не является корректным URL.'
        )
    
    def __call__(self, value: str) -> None:
        """
        Проверяет URL.
        
        Args:
            value (str): Проверяемый URL.
        
        Raises:
            ValidationError: Если значение не является корректным URL.
        """
        import urllib.parse
        
        try:
            parsed_url = urllib.parse.urlparse(value)
            
            if not parsed_url.scheme:
                raise ValidationError(
                    _('URL должен содержать схему (например, http://).'),
                    params={'value': value}
                )
            
            if parsed_url.scheme not in self.schemes:
                raise ValidationError(
                    _('URL содержит запрещенную схему: %(scheme)s. Разрешенные схемы: %(schemes)s.'),
                    params={'scheme': parsed_url.scheme, 'schemes': ', '.join(self.schemes), 'value': value}
                )
            
            if not parsed_url.netloc:
                raise ValidationError(
                    _('URL должен содержать домен.'),
                    params={'value': value}
                )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            
            raise ValidationError(
                self.message,
                params={'value': value}
            )

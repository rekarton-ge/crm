"""
Валидаторы для файлов.

Этот модуль содержит валидаторы для файлов.
"""

import os
import magic
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class FileExtensionValidator:
    """
    Валидатор для проверки расширения файла.
    
    Проверяет, что расширение файла входит в список разрешенных расширений.
    """
    
    def __init__(self, allowed_extensions: List[str], message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            allowed_extensions (List[str]): Список разрешенных расширений.
            message (str, optional): Сообщение об ошибке.
        """
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.message = message or _(
            'Расширение файла "%(extension)s" не разрешено. '
            'Разрешенные расширения: %(allowed_extensions)s.'
        )
    
    def __call__(self, value: UploadedFile) -> None:
        """
        Проверяет расширение файла.
        
        Args:
            value (UploadedFile): Загруженный файл.
        
        Raises:
            ValidationError: Если расширение файла не разрешено.
        """
        extension = os.path.splitext(value.name)[1].lower().lstrip('.')
        
        if extension not in self.allowed_extensions:
            raise ValidationError(
                self.message,
                params={
                    'extension': extension,
                    'allowed_extensions': ', '.join(self.allowed_extensions),
                    'value': value,
                }
            )


@deconstructible
class FileContentTypeValidator:
    """
    Валидатор для проверки типа содержимого файла.
    
    Проверяет, что тип содержимого файла входит в список разрешенных типов.
    """
    
    def __init__(self, allowed_content_types: List[str], message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            allowed_content_types (List[str]): Список разрешенных типов содержимого.
            message (str, optional): Сообщение об ошибке.
        """
        self.allowed_content_types = allowed_content_types
        self.message = message or _(
            'Тип содержимого файла "%(content_type)s" не разрешен. '
            'Разрешенные типы: %(allowed_content_types)s.'
        )
    
    def __call__(self, value: UploadedFile) -> None:
        """
        Проверяет тип содержимого файла.
        
        Args:
            value (UploadedFile): Загруженный файл.
        
        Raises:
            ValidationError: Если тип содержимого файла не разрешен.
        """
        content_type = value.content_type
        
        if content_type not in self.allowed_content_types:
            raise ValidationError(
                self.message,
                params={
                    'content_type': content_type,
                    'allowed_content_types': ', '.join(self.allowed_content_types),
                    'value': value,
                }
            )


@deconstructible
class FileSizeValidator:
    """
    Валидатор для проверки размера файла.
    
    Проверяет, что размер файла не превышает максимальный размер.
    """
    
    def __init__(self, max_size: int, message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            max_size (int): Максимальный размер файла в байтах.
            message (str, optional): Сообщение об ошибке.
        """
        self.max_size = max_size
        self.message = message or _(
            'Размер файла %(size)s превышает максимальный размер %(max_size)s.'
        )
    
    def __call__(self, value: UploadedFile) -> None:
        """
        Проверяет размер файла.
        
        Args:
            value (UploadedFile): Загруженный файл.
        
        Raises:
            ValidationError: Если размер файла превышает максимальный размер.
        """
        if value.size > self.max_size:
            raise ValidationError(
                self.message,
                params={
                    'size': self._format_size(value.size),
                    'max_size': self._format_size(self.max_size),
                    'value': value,
                }
            )
    
    def _format_size(self, size: int) -> str:
        """
        Форматирует размер файла.
        
        Args:
            size (int): Размер файла в байтах.
        
        Returns:
            str: Отформатированный размер файла.
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        
        return f"{size:.2f} PB"


@deconstructible
class FileTypeValidator:
    """
    Валидатор для проверки типа файла.
    
    Проверяет, что тип файла входит в список разрешенных типов.
    Использует библиотеку python-magic для определения типа файла.
    """
    
    def __init__(self, allowed_types: List[str], message: Optional[str] = None):
        """
        Инициализация валидатора.
        
        Args:
            allowed_types (List[str]): Список разрешенных типов файлов.
            message (str, optional): Сообщение об ошибке.
        """
        self.allowed_types = allowed_types
        self.message = message or _(
            'Тип файла "%(file_type)s" не разрешен. '
            'Разрешенные типы: %(allowed_types)s.'
        )
    
    def __call__(self, value: UploadedFile) -> None:
        """
        Проверяет тип файла.
        
        Args:
            value (UploadedFile): Загруженный файл.
        
        Raises:
            ValidationError: Если тип файла не разрешен.
        """
        try:
            file_type = magic.from_buffer(value.read(1024), mime=True)
            # Сбрасываем указатель файла в начало
            value.seek(0)
        except Exception as e:
            raise ValidationError(
                _('Не удалось определить тип файла: %(error)s'),
                params={'error': str(e), 'value': value}
            )
        
        if file_type not in self.allowed_types:
            raise ValidationError(
                self.message,
                params={
                    'file_type': file_type,
                    'allowed_types': ', '.join(self.allowed_types),
                    'value': value,
                }
            )


@deconstructible
class ImageDimensionsValidator:
    """
    Валидатор для проверки размеров изображения.
    
    Проверяет, что размеры изображения соответствуют ограничениям.
    """
    
    def __init__(
        self,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        message: Optional[str] = None
    ):
        """
        Инициализация валидатора.
        
        Args:
            min_width (int, optional): Минимальная ширина изображения.
            min_height (int, optional): Минимальная высота изображения.
            max_width (int, optional): Максимальная ширина изображения.
            max_height (int, optional): Максимальная высота изображения.
            message (str, optional): Сообщение об ошибке.
        """
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.message = message or _(
            'Размеры изображения (%(width)s x %(height)s) не соответствуют ограничениям: '
            '%(constraints)s.'
        )
    
    def __call__(self, value: UploadedFile) -> None:
        """
        Проверяет размеры изображения.
        
        Args:
            value (UploadedFile): Загруженное изображение.
        
        Raises:
            ValidationError: Если размеры изображения не соответствуют ограничениям.
        """
        from PIL import Image
        
        try:
            img = Image.open(value)
            width, height = img.size
            # Сбрасываем указатель файла в начало
            value.seek(0)
        except Exception as e:
            raise ValidationError(
                _('Не удалось определить размеры изображения: %(error)s'),
                params={'error': str(e), 'value': value}
            )
        
        constraints = []
        
        if self.min_width is not None and width < self.min_width:
            constraints.append(f'минимальная ширина {self.min_width}px')
        
        if self.min_height is not None and height < self.min_height:
            constraints.append(f'минимальная высота {self.min_height}px')
        
        if self.max_width is not None and width > self.max_width:
            constraints.append(f'максимальная ширина {self.max_width}px')
        
        if self.max_height is not None and height > self.max_height:
            constraints.append(f'максимальная высота {self.max_height}px')
        
        if constraints:
            raise ValidationError(
                self.message,
                params={
                    'width': width,
                    'height': height,
                    'constraints': ', '.join(constraints),
                    'value': value,
                }
            )

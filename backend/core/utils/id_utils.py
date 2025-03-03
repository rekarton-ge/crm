"""
Утилиты для генерации идентификаторов.

Этот модуль содержит функции для генерации различных типов идентификаторов,
включая UUID, короткие ID и референсные номера.
"""

import uuid
import random
import string
import time
from datetime import datetime


def generate_uuid():
    """
    Генерирует UUID.
    
    Returns:
        str: UUID в виде строки.
    """
    return str(uuid.uuid4())


def generate_short_id(length=8):
    """
    Генерирует короткий идентификатор.
    
    Args:
        length (int, optional): Длина идентификатора. По умолчанию 8.
    
    Returns:
        str: Короткий идентификатор.
    """
    if length < 1:
        return ""
    
    # Используем буквы и цифры для генерации идентификатора
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_reference_number(prefix="REF", length=10):
    """
    Генерирует референсный номер.
    
    Args:
        prefix (str, optional): Префикс номера. По умолчанию "REF".
        length (int, optional): Длина номера без префикса. По умолчанию 10.
    
    Returns:
        str: Референсный номер.
    """
    if length < 1:
        return prefix
    
    # Получаем текущую дату и время
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    
    # Получаем текущее время в миллисекундах
    time_part = str(int(time.time() * 1000))[-6:]
    
    # Генерируем случайную часть
    random_part = ''.join(random.choice(string.digits) for _ in range(length - len(date_part) - len(time_part)))
    
    # Собираем номер
    number = f"{date_part}{time_part}{random_part}"
    
    # Обрезаем номер до нужной длины
    if len(number) > length:
        number = number[:length]
    
    # Добавляем префикс
    if prefix:
        return f"{prefix}-{number}"
    
    return number 
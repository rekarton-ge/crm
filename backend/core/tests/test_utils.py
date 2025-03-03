"""
Тесты для утилит приложения Core.

Этот модуль содержит тесты для утилит приложения Core.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.utils.date_utils import (
    format_date, format_datetime, get_date_range, is_date_in_range,
    get_month_start_end, get_quarter_start_end, get_year_start_end
)
from core.utils.text_utils import (
    slugify, truncate_text, strip_tags, normalize_text, 
    generate_random_string, mask_sensitive_data
)
from core.utils.file_utils import (
    get_file_extension, get_file_size, get_mime_type, 
    is_valid_file_type, sanitize_filename
)
from core.utils.security_utils import (
    hash_password, verify_password, encrypt_data, decrypt_data,
    generate_token, validate_token
)
from core.utils.id_generators import (
    generate_uuid, generate_short_id, generate_reference_number
)

User = get_user_model()


class DateUtilsTest(TestCase):
    """
    Тесты для утилит работы с датами.
    """
    
    def test_format_date(self):
        """
        Тест форматирования даты.
        """
        date = datetime(2023, 1, 15).date()
        self.assertEqual(format_date(date), '15.01.2023')
        self.assertEqual(format_date(date, '%Y-%m-%d'), '2023-01-15')
    
    def test_format_datetime(self):
        """
        Тест форматирования даты и времени.
        """
        dt = datetime(2023, 1, 15, 14, 30, 45)
        self.assertEqual(format_datetime(dt), '15.01.2023 14:30:45')
        self.assertEqual(format_datetime(dt, '%Y-%m-%d %H:%M'), '2023-01-15 14:30')
    
    def test_get_date_range(self):
        """
        Тест получения диапазона дат.
        """
        start_date = datetime(2023, 1, 1).date()
        end_date = datetime(2023, 1, 5).date()
        date_range = get_date_range(start_date, end_date)
        self.assertEqual(len(date_range), 5)
        self.assertEqual(date_range[0], start_date)
        self.assertEqual(date_range[-1], end_date)
    
    def test_is_date_in_range(self):
        """
        Тест проверки вхождения даты в диапазон.
        """
        start_date = datetime(2023, 1, 1).date()
        end_date = datetime(2023, 1, 10).date()
        test_date = datetime(2023, 1, 5).date()
        self.assertTrue(is_date_in_range(test_date, start_date, end_date))
        
        test_date = datetime(2022, 12, 31).date()
        self.assertFalse(is_date_in_range(test_date, start_date, end_date))
        
        test_date = datetime(2023, 1, 11).date()
        self.assertFalse(is_date_in_range(test_date, start_date, end_date))
    
    def test_get_month_start_end(self):
        """
        Тест получения начала и конца месяца.
        """
        date = datetime(2023, 1, 15).date()
        start, end = get_month_start_end(date)
        self.assertEqual(start, datetime(2023, 1, 1).date())
        self.assertEqual(end, datetime(2023, 1, 31).date())
    
    def test_get_quarter_start_end(self):
        """
        Тест получения начала и конца квартала.
        """
        date = datetime(2023, 2, 15).date()  # Q1
        start, end = get_quarter_start_end(date)
        self.assertEqual(start, datetime(2023, 1, 1).date())
        self.assertEqual(end, datetime(2023, 3, 31).date())
        
        date = datetime(2023, 5, 15).date()  # Q2
        start, end = get_quarter_start_end(date)
        self.assertEqual(start, datetime(2023, 4, 1).date())
        self.assertEqual(end, datetime(2023, 6, 30).date())
    
    def test_get_year_start_end(self):
        """
        Тест получения начала и конца года.
        """
        date = datetime(2023, 6, 15).date()
        start, end = get_year_start_end(date)
        self.assertEqual(start, datetime(2023, 1, 1).date())
        self.assertEqual(end, datetime(2023, 12, 31).date())


class TextUtilsTest(TestCase):
    """
    Тесты для утилит работы с текстом.
    """
    
    def test_slugify(self):
        """
        Тест преобразования текста в slug.
        """
        self.assertEqual(slugify('Hello World'), 'hello-world')
        self.assertEqual(slugify('Привет, мир!'), 'privet-mir')
        self.assertEqual(slugify('Test 123'), 'test-123')
    
    def test_truncate_text(self):
        """
        Тест обрезки текста.
        """
        text = 'This is a long text that needs to be truncated'
        self.assertEqual(truncate_text(text, 10), 'This is a...')
        self.assertEqual(truncate_text(text, 10, '---'), 'This is a---')
        self.assertEqual(truncate_text('Short', 10), 'Short')
    
    def test_strip_tags(self):
        """
        Тест удаления HTML-тегов.
        """
        html = '<p>This is <b>bold</b> text with <a href="#">link</a></p>'
        self.assertEqual(strip_tags(html), 'This is bold text with link')
    
    def test_normalize_text(self):
        """
        Тест нормализации текста.
        """
        text = '  Multiple    spaces   and\ttabs\nand newlines  '
        self.assertEqual(normalize_text(text), 'Multiple spaces and tabs and newlines')
    
    def test_generate_random_string(self):
        """
        Тест генерации случайной строки.
        """
        random_string = generate_random_string(10)
        self.assertEqual(len(random_string), 10)
        
        # Проверяем, что две случайные строки различаются
        another_random_string = generate_random_string(10)
        self.assertNotEqual(random_string, another_random_string)
    
    def test_mask_sensitive_data(self):
        """
        Тест маскирования конфиденциальных данных.
        """
        self.assertEqual(mask_sensitive_data('1234567890123456'), '************3456')
        self.assertEqual(mask_sensitive_data('test@example.com', mask_char='*'), '****@example.com')
        self.assertEqual(mask_sensitive_data('short', reveal_chars=2), '***rt')


class FileUtilsTest(TestCase):
    """
    Тесты для утилит работы с файлами.
    """
    
    def test_get_file_extension(self):
        """
        Тест получения расширения файла.
        """
        self.assertEqual(get_file_extension('document.pdf'), 'pdf')
        self.assertEqual(get_file_extension('image.jpg'), 'jpg')
        self.assertEqual(get_file_extension('archive.tar.gz'), 'gz')
        self.assertEqual(get_file_extension('noextension'), '')
    
    def test_get_file_size(self):
        """
        Тест получения размера файла в человекочитаемом формате.
        """
        self.assertEqual(get_file_size(1024), '1.0 KB')
        self.assertEqual(get_file_size(1048576), '1.0 MB')
        self.assertEqual(get_file_size(1073741824), '1.0 GB')
        self.assertEqual(get_file_size(500), '500.0 B')
    
    @patch('mimetypes.guess_type')
    def test_get_mime_type(self, mock_guess_type):
        """
        Тест получения MIME-типа файла.
        """
        mock_guess_type.return_value = ('application/pdf', None)
        self.assertEqual(get_mime_type('document.pdf'), 'application/pdf')
        
        mock_guess_type.return_value = ('image/jpeg', None)
        self.assertEqual(get_mime_type('image.jpg'), 'image/jpeg')
        
        mock_guess_type.return_value = (None, None)
        self.assertEqual(get_mime_type('unknown'), 'application/octet-stream')
    
    def test_is_valid_file_type(self):
        """
        Тест проверки типа файла.
        """
        self.assertTrue(is_valid_file_type('document.pdf', ['pdf', 'doc', 'docx']))
        self.assertTrue(is_valid_file_type('image.jpg', ['jpg', 'jpeg', 'png']))
        self.assertFalse(is_valid_file_type('script.js', ['pdf', 'doc', 'docx']))
    
    def test_sanitize_filename(self):
        """
        Тест очистки имени файла.
        """
        self.assertEqual(sanitize_filename('file with spaces.pdf'), 'file_with_spaces.pdf')
        self.assertEqual(sanitize_filename('file/with/slashes.pdf'), 'file_with_slashes.pdf')
        self.assertEqual(sanitize_filename('file<with>special&chars.pdf'), 'file_with_special_chars.pdf')


class SecurityUtilsTest(TestCase):
    """
    Тесты для утилит безопасности.
    """
    
    def test_hash_password(self):
        """
        Тест хеширования пароля.
        """
        password = 'secure_password'
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith('$2'))  # bcrypt hash
    
    def test_verify_password(self):
        """
        Тест проверки пароля.
        """
        password = 'secure_password'
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password('wrong_password', hashed))
    
    def test_encrypt_decrypt_data(self):
        """
        Тест шифрования и дешифрования данных.
        """
        data = 'sensitive information'
        key = 'secret_key'
        encrypted = encrypt_data(data, key)
        self.assertNotEqual(data, encrypted)
        
        decrypted = decrypt_data(encrypted, key)
        self.assertEqual(data, decrypted)
    
    def test_generate_validate_token(self):
        """
        Тест генерации и проверки токена.
        """
        user_id = 123
        token = generate_token(user_id)
        self.assertTrue(validate_token(token))
        
        # Проверяем, что токен с истекшим сроком действия не валиден
        self.assertFalse(validate_token("invalid_token"))


class IdGeneratorsTest(TestCase):
    """
    Тесты для генераторов идентификаторов.
    """
    
    def test_generate_uuid(self):
        """
        Тест генерации UUID.
        """
        uuid = generate_uuid()
        self.assertEqual(len(uuid), 36)  # UUID в формате строки имеет длину 36 символов
        
        # Проверяем, что два UUID различаются
        another_uuid = generate_uuid()
        self.assertNotEqual(uuid, another_uuid)
    
    def test_generate_short_id(self):
        """
        Тест генерации короткого идентификатора.
        """
        short_id = generate_short_id()
        self.assertEqual(len(short_id), 8)  # По умолчанию длина 8 символов
        
        # Проверяем с указанной длиной
        short_id = generate_short_id(length=12)
        self.assertEqual(len(short_id), 12)
        
        # Проверяем с указанным префиксом
        short_id = generate_short_id(prefix='TST-')
        self.assertTrue(short_id.startswith('TST-'))
        self.assertEqual(len(short_id), 12)  # 'TST-' + 8 символов
    
    def test_generate_reference_number(self):
        """
        Тест генерации номера ссылки.
        """
        ref_num = generate_reference_number()
        self.assertEqual(len(ref_num), 10)  # По умолчанию длина 10 символов
        
        # Проверяем с указанным префиксом и длиной
        ref_num = generate_reference_number(prefix='INV', length=8)
        self.assertTrue(ref_num.startswith('INV'))
        self.assertEqual(len(ref_num), 11)  # 'INV' + 8 символов
        
        # Проверяем с указанной датой
        ref_num = generate_reference_number(include_date=True)
        date_part = datetime.now().strftime('%Y%m%d')
        self.assertTrue(date_part in ref_num)


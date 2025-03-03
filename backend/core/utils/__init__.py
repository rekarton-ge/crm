"""
Пакет утилит для модуля Core.

Этот пакет содержит различные утилиты, используемые в модуле Core.
"""

# Утилиты для работы с датами
from core.utils.date_utils import (
    get_current_timezone, localize_datetime, format_datetime, format_date,
    parse_datetime, parse_date, get_date_range, get_month_start_end,
    get_week_start_end, get_quarter_start_end, get_year_start_end
)

# Утилиты для работы с текстом
from core.utils.text_utils import (
    slugify, generate_random_string, truncate_string, strip_tags,
    normalize_text, remove_accents, camel_to_snake, snake_to_camel,
    snake_to_title, is_valid_email, is_valid_phone, format_phone
)

# Утилиты для работы с файлами
from core.utils.file_utils import (
    get_file_extension, get_file_name, get_file_size, get_file_mime_type,
    is_allowed_file_type, generate_unique_filename, save_uploaded_file,
    get_file_hash, create_directory, get_media_url, get_file_content,
    get_file_content_as_string, write_file_content
)

# Утилиты для генерации идентификаторов
from core.utils.id_generators import (
    generate_uuid, generate_uuid_without_hyphens, generate_short_uuid,
    generate_random_string, generate_random_digits, generate_timestamp_id,
    generate_slug, generate_unique_slug, generate_hash, generate_short_hash,
    generate_reference_code
)

# Утилиты для работы с запросами к базе данных
from core.utils.query_utils import (
    paginate_queryset, filter_by_date_range, filter_by_text, filter_by_related,
    filter_by_boolean, order_queryset, annotate_count, annotate_sum,
    annotate_avg, get_or_none, bulk_update_or_create
)

# Утилиты для обеспечения безопасности
from core.utils.security_utils import (
    generate_secure_token, generate_secure_password, hash_password,
    verify_password, generate_hmac_signature, verify_hmac_signature,
    encrypt_data, decrypt_data, is_valid_password
)

__all__ = [
    # Утилиты для работы с датами
    'get_current_timezone',
    'localize_datetime',
    'format_datetime',
    'format_date',
    'parse_datetime',
    'parse_date',
    'get_date_range',
    'get_month_start_end',
    'get_week_start_end',
    'get_quarter_start_end',
    'get_year_start_end',
    
    # Утилиты для работы с текстом
    'slugify',
    'generate_random_string',
    'truncate_string',
    'strip_tags',
    'normalize_text',
    'remove_accents',
    'camel_to_snake',
    'snake_to_camel',
    'snake_to_title',
    'is_valid_email',
    'is_valid_phone',
    'format_phone',
    
    # Утилиты для работы с файлами
    'get_file_extension',
    'get_file_name',
    'get_file_size',
    'get_file_mime_type',
    'is_allowed_file_type',
    'generate_unique_filename',
    'save_uploaded_file',
    'get_file_hash',
    'create_directory',
    'get_media_url',
    'get_file_content',
    'get_file_content_as_string',
    'write_file_content',
    
    # Утилиты для генерации идентификаторов
    'generate_uuid',
    'generate_uuid_without_hyphens',
    'generate_short_uuid',
    'generate_random_string',
    'generate_random_digits',
    'generate_timestamp_id',
    'generate_slug',
    'generate_unique_slug',
    'generate_hash',
    'generate_short_hash',
    'generate_reference_code',
    
    # Утилиты для работы с запросами к базе данных
    'paginate_queryset',
    'filter_by_date_range',
    'filter_by_text',
    'filter_by_related',
    'filter_by_boolean',
    'order_queryset',
    'annotate_count',
    'annotate_sum',
    'annotate_avg',
    'get_or_none',
    'bulk_update_or_create',
    
    # Утилиты для обеспечения безопасности
    'generate_secure_token',
    'generate_secure_password',
    'hash_password',
    'verify_password',
    'generate_hmac_signature',
    'verify_hmac_signature',
    'encrypt_data',
    'decrypt_data',
    'is_valid_password',
]

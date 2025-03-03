"""
Пакет моделей для модуля Core.

Этот пакет содержит все модели, используемые в модуле Core.
"""

# Базовые модели
from core.models.base import (
    TimeStampedModel, UserStampedModel, SoftDeleteModel, BaseModel
)

# Модели метаданных
from core.models.metadata import (
    Setting, Category
)

# Модели аудита
from core.models.audit import (
    AuditLog, LoginAttempt
)

# Модели шаблонов
from core.models.templates import (
    TemplateCategory, Template, TemplateVersion
)

# Модели уведомлений
from core.models.notifications import (
    NotificationChannel, NotificationType, Notification, UserNotificationPreference
)

# Модели настроек
from core.models.settings import (
    SystemSetting, UserSetting, Theme
)

# Модели тегов
from core.models.tags import (
    TagGroup, Tag, TaggedItem
)

__all__ = [
    # Базовые модели
    'TimeStampedModel',
    'UserStampedModel',
    'SoftDeleteModel',
    'BaseModel',
    
    # Модели метаданных
    'Setting',
    'Category',
    
    # Модели аудита
    'AuditLog',
    'LoginAttempt',
    
    # Модели шаблонов
    'TemplateCategory',
    'Template',
    'TemplateVersion',
    
    # Модели уведомлений
    'NotificationChannel',
    'NotificationType',
    'Notification',
    'UserNotificationPreference',
    
    # Модели настроек
    'SystemSetting',
    'UserSetting',
    'Theme',
    
    # Модели тегов
    'TagGroup',
    'Tag',
    'TaggedItem',
]

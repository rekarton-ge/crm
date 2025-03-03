"""
Сигналы для приложения.

Этот пакет содержит сигналы и обработчики сигналов для приложения Django.
"""

from core.signals.handlers import (
    handle_user_created, handle_user_updated, handle_user_deleted,
    handle_tag_created, handle_tag_updated, handle_tag_deleted,
    handle_notification_created, handle_notification_read,
    handle_template_created, handle_template_updated, handle_template_deleted,
    handle_setting_changed
)


__all__ = [
    'handle_user_created',
    'handle_user_updated',
    'handle_user_deleted',
    'handle_tag_created',
    'handle_tag_updated',
    'handle_tag_deleted',
    'handle_notification_created',
    'handle_notification_read',
    'handle_template_created',
    'handle_template_updated',
    'handle_template_deleted',
    'handle_setting_changed',
]

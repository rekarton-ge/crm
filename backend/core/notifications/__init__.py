"""
Система уведомлений.

Этот пакет содержит компоненты для работы с уведомлениями, включая базовые классы,
реализации для различных каналов уведомлений и шаблоны.
"""

from core.notifications.base import (
    BaseNotification, NotificationManager, NotificationChannel, NotificationTemplate
)
from core.notifications.email_notifications import EmailNotification, EmailNotificationChannel
from core.notifications.push_notifications import PushNotification, PushNotificationChannel
from core.notifications.web_notifications import WebNotification, WebNotificationChannel


__all__ = [
    'BaseNotification',
    'NotificationManager',
    'NotificationChannel',
    'NotificationTemplate',
    'EmailNotification',
    'EmailNotificationChannel',
    'PushNotification',
    'PushNotificationChannel',
    'WebNotification',
    'WebNotificationChannel',
]

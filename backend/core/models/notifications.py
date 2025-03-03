"""
Модели для работы с уведомлениями в системе.

Этот модуль содержит модели для хранения и управления уведомлениями,
которые отправляются пользователям системы.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from core.models.base import BaseModel

User = get_user_model()


class NotificationChannel(BaseModel):
    """
    Модель для хранения каналов уведомлений.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    
    class Meta:
        verbose_name = _("Канал уведомлений")
        verbose_name_plural = _("Каналы уведомлений")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class NotificationType(BaseModel):
    """
    Модель для хранения типов уведомлений.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    template = models.ForeignKey(
        "core.Template",
        verbose_name=_("Шаблон"),
        related_name="notification_types",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    channels = models.ManyToManyField(
        NotificationChannel,
        verbose_name=_("Каналы"),
        related_name="notification_types",
        blank=True
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    
    class Meta:
        verbose_name = _("Тип уведомления")
        verbose_name_plural = _("Типы уведомлений")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Notification(BaseModel):
    """
    Модель для хранения уведомлений.
    """
    STATUS_CHOICES = (
        ('pending', _('Ожидает отправки')),
        ('sent', _('Отправлено')),
        ('delivered', _('Доставлено')),
        ('read', _('Прочитано')),
        ('failed', _('Ошибка')),
    )
    
    user = models.ForeignKey(
        User,
        verbose_name=_("Пользователь"),
        related_name="notifications",
        on_delete=models.CASCADE
    )
    notification_type = models.ForeignKey(
        NotificationType,
        verbose_name=_("Тип уведомления"),
        related_name="notifications",
        on_delete=models.CASCADE
    )
    channel = models.ForeignKey(
        NotificationChannel,
        verbose_name=_("Канал"),
        related_name="notifications",
        on_delete=models.CASCADE
    )
    title = models.CharField(_("Заголовок"), max_length=255)
    content = models.TextField(_("Содержимое"))
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default='pending')
    read_at = models.DateTimeField(_("Дата прочтения"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Дата отправки"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Дата доставки"), null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Тип контента"),
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(_("ID объекта"), max_length=255, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    data = models.JSONField(_("Данные"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["status"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user} - {self.get_status_display()}"


class UserNotificationPreference(BaseModel):
    """
    Модель для хранения предпочтений пользователей по уведомлениям.
    """
    user = models.ForeignKey(
        User,
        verbose_name=_("Пользователь"),
        related_name="notification_preferences",
        on_delete=models.CASCADE
    )
    notification_type = models.ForeignKey(
        NotificationType,
        verbose_name=_("Тип уведомления"),
        related_name="user_preferences",
        on_delete=models.CASCADE
    )
    channel = models.ForeignKey(
        NotificationChannel,
        verbose_name=_("Канал"),
        related_name="user_preferences",
        on_delete=models.CASCADE
    )
    is_enabled = models.BooleanField(_("Включено"), default=True)
    
    class Meta:
        verbose_name = _("Предпочтение пользователя по уведомлениям")
        verbose_name_plural = _("Предпочтения пользователей по уведомлениям")
        unique_together = [["user", "notification_type", "channel"]]
    
    def __str__(self):
        return f"{self.user} - {self.notification_type} - {self.channel}"

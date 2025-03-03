"""
Модели для аудита действий пользователей в системе.

Этот модуль содержит модели для отслеживания и хранения информации
о действиях пользователей в системе.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from core.models.base import TimeStampedModel

User = get_user_model()


class AuditLog(TimeStampedModel):
    """
    Модель для хранения записей аудита действий пользователей.
    """
    ACTION_CHOICES = (
        ('create', _('Создание')),
        ('update', _('Обновление')),
        ('delete', _('Удаление')),
        ('view', _('Просмотр')),
        ('login', _('Вход в систему')),
        ('logout', _('Выход из системы')),
        ('export', _('Экспорт данных')),
        ('import', _('Импорт данных')),
        ('other', _('Другое')),
    )
    
    user = models.ForeignKey(
        User,
        verbose_name=_("Пользователь"),
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(_("Действие"), max_length=20, choices=ACTION_CHOICES)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Тип контента"),
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(_("ID объекта"), max_length=255, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(_("Представление объекта"), max_length=255, blank=True)
    data = models.JSONField(_("Данные"), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_("IP-адрес"), null=True, blank=True)
    user_agent = models.TextField(_("User-Agent"), blank=True)
    
    class Meta:
        verbose_name = _("Запись аудита")
        verbose_name_plural = _("Записи аудита")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["action"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.user} - {self.created_at}"


class LoginAttempt(TimeStampedModel):
    """
    Модель для хранения информации о попытках входа в систему.
    """
    STATUS_CHOICES = (
        ('success', _('Успешно')),
        ('failed', _('Неудачно')),
    )
    
    username = models.CharField(_("Имя пользователя"), max_length=255)
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(_("IP-адрес"), null=True, blank=True)
    user_agent = models.TextField(_("User-Agent"), blank=True)
    user = models.ForeignKey(
        User,
        verbose_name=_("Пользователь"),
        related_name="login_attempts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Попытка входа")
        verbose_name_plural = _("Попытки входа")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["status"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_status_display()} - {self.created_at}"

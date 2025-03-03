"""
Модели для работы с настройками системы.

Этот модуль содержит модели для хранения и управления настройками системы,
включая пользовательские настройки и глобальные параметры.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from core.models.base import BaseModel

User = get_user_model()


class SystemSetting(BaseModel):
    """
    Модель для хранения глобальных настроек системы.
    """
    GROUP_CHOICES = (
        ('general', _('Общие')),
        ('security', _('Безопасность')),
        ('email', _('Email')),
        ('notification', _('Уведомления')),
        ('integration', _('Интеграции')),
        ('appearance', _('Внешний вид')),
        ('other', _('Другое')),
    )
    
    key = models.CharField(_("Ключ"), max_length=100, unique=True)
    value = models.JSONField(_("Значение"))
    description = models.TextField(_("Описание"), blank=True)
    group = models.CharField(_("Группа"), max_length=20, choices=GROUP_CHOICES, default='general')
    is_public = models.BooleanField(_("Публичная"), default=False)
    is_editable = models.BooleanField(_("Редактируемая"), default=True)
    
    class Meta:
        verbose_name = _("Системная настройка")
        verbose_name_plural = _("Системные настройки")
        ordering = ["group", "key"]
        indexes = [
            models.Index(fields=["group"]),
            models.Index(fields=["is_public"]),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.get_group_display()})"


class UserSetting(BaseModel):
    """
    Модель для хранения пользовательских настроек.
    """
    user = models.ForeignKey(
        User,
        verbose_name=_("Пользователь"),
        related_name="settings",
        on_delete=models.CASCADE
    )
    key = models.CharField(_("Ключ"), max_length=100)
    value = models.JSONField(_("Значение"))
    
    class Meta:
        verbose_name = _("Пользовательская настройка")
        verbose_name_plural = _("Пользовательские настройки")
        unique_together = [["user", "key"]]
        ordering = ["user", "key"]
    
    def __str__(self):
        return f"{self.user} - {self.key}"


class Theme(BaseModel):
    """
    Модель для хранения тем оформления.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    colors = models.JSONField(_("Цвета"), default=dict)
    is_default = models.BooleanField(_("По умолчанию"), default=False)
    is_active = models.BooleanField(_("Активна"), default=True)
    
    class Meta:
        verbose_name = _("Тема оформления")
        verbose_name_plural = _("Темы оформления")
        ordering = ["-is_default", "name"]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Переопределение метода сохранения для обеспечения уникальности темы по умолчанию.
        """
        if self.is_default:
            # Если текущая тема устанавливается как тема по умолчанию,
            # сбрасываем флаг is_default у всех других тем
            Theme.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

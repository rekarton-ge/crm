"""
Модели для работы с метаданными в системе.

Этот модуль содержит модели для хранения и управления метаданными,
такими как категории и настройки.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.base import BaseModel


class Setting(BaseModel):
    """
    Модель для хранения настроек системы.
    """
    key = models.CharField(_("Ключ"), max_length=100, unique=True)
    value = models.JSONField(_("Значение"))
    description = models.TextField(_("Описание"), blank=True)
    is_public = models.BooleanField(_("Публичная"), default=False)
    
    class Meta:
        verbose_name = _("Настройка")
        verbose_name_plural = _("Настройки")
        ordering = ["key"]
    
    def __str__(self):
        return self.key


class Category(BaseModel):
    """
    Модель для хранения категорий, которые могут быть применены к различным объектам.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Родительская категория"),
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ["name"]
    
    def __str__(self):
        return self.name

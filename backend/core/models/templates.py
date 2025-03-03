"""
Модели для работы с шаблонами в системе.

Этот модуль содержит модели для хранения и управления шаблонами,
которые используются для генерации документов, писем и других материалов.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.base import BaseModel


class TemplateCategory(BaseModel):
    """
    Модель для категоризации шаблонов.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    
    class Meta:
        verbose_name = _("Категория шаблонов")
        verbose_name_plural = _("Категории шаблонов")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Template(BaseModel):
    """
    Модель для хранения шаблонов.
    """
    TYPE_CHOICES = (
        ('email', _('Email')),
        ('document', _('Документ')),
        ('sms', _('SMS')),
        ('notification', _('Уведомление')),
        ('other', _('Другое')),
    )
    
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    category = models.ForeignKey(
        TemplateCategory,
        verbose_name=_("Категория"),
        related_name="templates",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    type = models.CharField(_("Тип"), max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField(_("Тема"), max_length=255, blank=True)
    content = models.TextField(_("Содержимое"))
    variables = models.JSONField(_("Переменные"), default=dict, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    
    class Meta:
        verbose_name = _("Шаблон")
        verbose_name_plural = _("Шаблоны")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["is_active"]),
        ]
    
    def __str__(self):
        return self.name


class TemplateVersion(BaseModel):
    """
    Модель для хранения версий шаблонов.
    """
    template = models.ForeignKey(
        Template,
        verbose_name=_("Шаблон"),
        related_name="versions",
        on_delete=models.CASCADE
    )
    version = models.PositiveIntegerField(_("Версия"))
    subject = models.CharField(_("Тема"), max_length=255, blank=True)
    content = models.TextField(_("Содержимое"))
    variables = models.JSONField(_("Переменные"), default=dict, blank=True)
    is_active = models.BooleanField(_("Активна"), default=False)
    
    class Meta:
        verbose_name = _("Версия шаблона")
        verbose_name_plural = _("Версии шаблонов")
        ordering = ["-version"]
        unique_together = [["template", "version"]]
    
    def __str__(self):
        return f"{self.template.name} - v{self.version}"

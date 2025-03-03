"""
Модели для работы с тегами в системе.

Этот модуль содержит модели для хранения и управления тегами,
которые могут быть применены к различным объектам системы.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from core.models.base import BaseModel
from core.models.metadata import Category


class TagGroup(BaseModel):
    """
    Модель для группировки тегов.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    
    class Meta:
        verbose_name = _("Группа тегов")
        verbose_name_plural = _("Группы тегов")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Tag(BaseModel):
    """
    Модель для хранения тегов.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    color = models.CharField(_("Цвет"), max_length=20, blank=True)
    group = models.ForeignKey(
        TagGroup,
        verbose_name=_("Группа"),
        related_name="tags",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("Категория"),
        related_name="tags",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Переопределение метода сохранения для автоматического создания slug.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TaggedItem(BaseModel):
    """
    Модель для связи тегов с различными объектами через GenericForeignKey.
    """
    tag = models.ForeignKey(
        Tag,
        verbose_name=_("Тег"),
        related_name="tagged_items",
        on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Тип контента"),
        on_delete=models.CASCADE
    )
    object_id = models.CharField(_("ID объекта"), max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")
    
    class Meta:
        verbose_name = _("Тегированный элемент")
        verbose_name_plural = _("Тегированные элементы")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        unique_together = [["tag", "content_type", "object_id"]]
    
    def __str__(self):
        return f"{self.tag.name} - {self.content_object}"

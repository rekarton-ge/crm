"""
Миксины для моделей.

Этот модуль содержит миксины для моделей Django.
"""

import uuid
from typing import Any, Dict, List, Optional, Type, Union

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    """
    Миксин для добавления полей created_at и updated_at.
    
    Добавляет поля created_at и updated_at, которые автоматически
    заполняются при создании и обновлении объекта.
    """
    
    created_at = models.DateTimeField(
        _('дата создания'),
        auto_now_add=True,
        db_index=True,
        help_text=_('Дата и время создания объекта')
    )
    updated_at = models.DateTimeField(
        _('дата обновления'),
        auto_now=True,
        help_text=_('Дата и время последнего обновления объекта')
    )
    
    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    """
    Миксин для добавления поля uuid.
    
    Добавляет поле uuid, которое автоматически заполняется
    при создании объекта.
    """
    
    uuid = models.UUIDField(
        _('UUID'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Уникальный идентификатор объекта')
    )
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Миксин для мягкого удаления объектов.
    
    Добавляет поле is_deleted и методы для мягкого удаления объектов.
    """
    
    is_deleted = models.BooleanField(
        _('удален'),
        default=False,
        db_index=True,
        help_text=_('Флаг, указывающий, что объект удален')
    )
    deleted_at = models.DateTimeField(
        _('дата удаления'),
        null=True,
        blank=True,
        help_text=_('Дата и время удаления объекта')
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """
        Мягкое удаление объекта.
        
        Args:
            using: Имя базы данных для удаления.
            keep_parents: Флаг, указывающий, нужно ли сохранять родительские объекты.
        
        Returns:
            Tuple[int, Dict[str, int]]: Количество удаленных объектов и словарь с количеством
                удаленных объектов по типам.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
        return (1, {'core.SoftDeleteMixin': 1})
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Жесткое удаление объекта.
        
        Args:
            using: Имя базы данных для удаления.
            keep_parents: Флаг, указывающий, нужно ли сохранять родительские объекты.
        
        Returns:
            Tuple[int, Dict[str, int]]: Количество удаленных объектов и словарь с количеством
                удаленных объектов по типам.
        """
        return super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """
        Восстановление удаленного объекта.
        
        Returns:
            Self: Восстановленный объект.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
        return self


class ActiveMixin(models.Model):
    """
    Миксин для добавления поля is_active.
    
    Добавляет поле is_active, которое указывает, активен ли объект.
    """
    
    is_active = models.BooleanField(
        _('активен'),
        default=True,
        db_index=True,
        help_text=_('Флаг, указывающий, что объект активен')
    )
    
    class Meta:
        abstract = True
    
    def activate(self):
        """
        Активация объекта.
        
        Returns:
            Self: Активированный объект.
        """
        self.is_active = True
        self.save(update_fields=['is_active'])
        return self
    
    def deactivate(self):
        """
        Деактивация объекта.
        
        Returns:
            Self: Деактивированный объект.
        """
        self.is_active = False
        self.save(update_fields=['is_active'])
        return self


class OrderableMixin(models.Model):
    """
    Миксин для добавления поля order.
    
    Добавляет поле order, которое указывает порядок объекта.
    """
    
    order = models.PositiveIntegerField(
        _('порядок'),
        default=0,
        db_index=True,
        help_text=_('Порядок отображения объекта')
    )
    
    class Meta:
        abstract = True
        ordering = ['order']


class SlugMixin(models.Model):
    """
    Миксин для добавления поля slug.
    
    Добавляет поле slug, которое используется для URL.
    """
    
    slug = models.SlugField(
        _('slug'),
        max_length=255,
        unique=True,
        help_text=_('Уникальный идентификатор для URL')
    )
    
    class Meta:
        abstract = True


class DescriptionMixin(models.Model):
    """
    Миксин для добавления поля description.
    
    Добавляет поле description, которое содержит описание объекта.
    """
    
    description = models.TextField(
        _('описание'),
        blank=True,
        help_text=_('Описание объекта')
    )
    
    class Meta:
        abstract = True


class MetadataMixin(models.Model):
    """
    Миксин для добавления поля metadata.
    
    Добавляет поле metadata, которое содержит дополнительные данные объекта.
    """
    
    metadata = models.JSONField(
        _('метаданные'),
        default=dict,
        blank=True,
        help_text=_('Дополнительные данные объекта')
    )
    
    class Meta:
        abstract = True
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Получение значения метаданных по ключу.
        
        Args:
            key (str): Ключ метаданных.
            default (Any, optional): Значение по умолчанию.
        
        Returns:
            Any: Значение метаданных.
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Установка значения метаданных по ключу.
        
        Args:
            key (str): Ключ метаданных.
            value (Any): Значение метаданных.
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata'])
    
    def delete_metadata(self, key: str) -> None:
        """
        Удаление значения метаданных по ключу.
        
        Args:
            key (str): Ключ метаданных.
        """
        if key in self.metadata:
            del self.metadata[key]
            self.save(update_fields=['metadata'])
    
    def clear_metadata(self) -> None:
        """
        Очистка всех метаданных.
        """
        self.metadata = {}
        self.save(update_fields=['metadata'])

"""
Базовые модели для всех сущностей системы.

Этот модуль содержит абстрактные базовые классы, которые используются
для наследования другими моделями в системе.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Абстрактная модель, добавляющая поля для отслеживания времени создания и обновления.
    """
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    """
    Абстрактная модель, добавляющая поля для отслеживания пользователей, создавших и обновивших запись.
    """
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Создано пользователем"),
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User,
        verbose_name=_("Обновлено пользователем"),
        related_name="%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Абстрактная модель, добавляющая функциональность мягкого удаления.
    """
    is_deleted = models.BooleanField(_("Удалено"), default=False)
    deleted_at = models.DateTimeField(_("Дата удаления"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        verbose_name=_("Удалено пользователем"),
        related_name="%(class)s_deleted",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def delete(self, deleted_by=None, *args, **kwargs):
        """
        Переопределение метода удаления для реализации мягкого удаления.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if deleted_by:
            self.deleted_by = deleted_by
        self.save()

    def hard_delete(self, *args, **kwargs):
        """
        Метод для фактического удаления объекта из базы данных.
        """
        super().delete(*args, **kwargs)


class BaseModel(TimeStampedModel, UserStampedModel, SoftDeleteModel):
    """
    Базовая модель, объединяющая функциональность отслеживания времени,
    пользователей и мягкого удаления.
    """
    class Meta:
        abstract = True

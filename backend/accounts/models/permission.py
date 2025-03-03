from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class CustomPermission(models.Model):
    """
    Расширение стандартных разрешений Django.
    Позволяет создавать кастомные разрешения для любых моделей.
    """
    codename = models.CharField(
        _('Кодовое имя разрешения'),
        max_length=100,
        unique=True,
        help_text=_('Техническое название разрешения, например: "can_approve_orders"')
    )

    name = models.CharField(
        _('Человекочитаемое название'),
        max_length=255,
        help_text=_('Понятное название разрешения, например: "Может утверждать заказы"')
    )

    description = models.TextField(
        _('Подробное описание'),
        blank=True,
        help_text=_('Детальное описание того, что позволяет делать это разрешение')
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Тип контента'),
        help_text=_('Модель, к которой применяется разрешение')
    )

    is_custom = models.BooleanField(
        _('Признак кастомного разрешения'),
        default=True,
        help_text=_('Если True, то это разрешение создано пользователем, а не системой')
    )

    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('разрешение')
        verbose_name_plural = _('разрешения')
        ordering = ['codename']
        unique_together = [['codename', 'content_type']]

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create_permission(cls, codename, name, description='', content_type=None):
        """
        Получает или создает разрешение с указанными параметрами
        """
        permission, created = cls.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={
                'name': name,
                'description': description,
                'is_custom': True
            }
        )
        return permission
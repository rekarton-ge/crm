"""
Модели для работы с сессиями пользователей.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserSession(models.Model):
    """
    Модель для хранения информации о сессиях пользователей.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('Пользователь')
    )

    session_key = models.CharField(
        _('Ключ сессии'),
        max_length=1024
    )

    ip_address = models.GenericIPAddressField(
        _('IP адрес'),
        null=True,
        blank=True
    )

    user_agent = models.CharField(
        _('User Agent'),
        max_length=255,
        blank=True
    )

    device_type = models.CharField(
        _('Тип устройства'),
        max_length=20,
        choices=[
            ('desktop', _('Компьютер')),
            ('mobile', _('Мобильное устройство')),
            ('tablet', _('Планшет')),
            ('other', _('Другое'))
        ],
        default='other'
    )

    location = models.CharField(
        _('Местоположение'),
        max_length=255,
        blank=True
    )

    started_at = models.DateTimeField(
        _('Время начала'),
        auto_now_add=True
    )

    last_activity = models.DateTimeField(
        _('Последняя активность'),
        auto_now=True
    )

    ended_at = models.DateTimeField(
        _('Время завершения'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('сессия пользователя')
        verbose_name_plural = _('сессии пользователей')
        ordering = ['-started_at']

    def __str__(self):
        return f'Сессия {self.user.username} от {self.started_at}'

    @classmethod
    def get_active_sessions(cls, user):
        """
        Возвращает активные сессии пользователя.
        """
        return cls.objects.filter(
            user=user,
            ended_at__isnull=True
        )

    def end_session(self):
        """
        Завершает текущую сессию.
        """
        self.ended_at = timezone.now()
        self.save(update_fields=['ended_at']) 
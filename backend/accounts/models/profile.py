from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """
    Модель профиля пользователя с дополнительной информацией.
    Связана с моделью User отношением один-к-одному.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Пользователь')
    )

    avatar = models.ImageField(
        _('Аватар'),
        upload_to='avatars/',
        null=True,
        blank=True
    )

    position = models.CharField(
        _('Должность'),
        max_length=100,
        blank=True
    )

    department = models.CharField(
        _('Отдел'),
        max_length=100,
        blank=True
    )

    bio = models.TextField(
        _('Краткая биография'),
        blank=True
    )

    date_of_birth = models.DateField(
        _('Дата рождения'),
        null=True,
        blank=True
    )

    ui_settings = models.JSONField(
        _('Настройки интерфейса'),
        default=dict
    )

    notification_settings = models.JSONField(
        _('Настройки уведомлений'),
        default=dict
    )

    language = models.CharField(
        _('Предпочитаемый язык'),
        max_length=10,
        default='ru'
    )

    timezone = models.CharField(
        _('Часовой пояс'),
        max_length=50,
        default='Europe/Moscow'
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
        verbose_name = _('профиль пользователя')
        verbose_name_plural = _('профили пользователей')

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

    def get_default_ui_settings(self):
        """
        Возвращает настройки интерфейса по умолчанию
        """
        return {
            'theme': 'light',
            'dashboard_layout': 'compact',
            'sidebar_collapsed': False,
            'notifications_position': 'top-right'
        }

    def get_default_notification_settings(self):
        """
        Возвращает настройки уведомлений по умолчанию
        """
        return {
            'email': True,
            'web': True,
            'push': False,
            'digest': 'daily'
        }

    def save(self, *args, **kwargs):
        """
        Переопределяем метод save для установки настроек по умолчанию,
        если они не были заданы
        """
        if not self.ui_settings:
            self.ui_settings = self.get_default_ui_settings()

        if not self.notification_settings:
            self.notification_settings = self.get_default_notification_settings()

        super().save(*args, **kwargs)
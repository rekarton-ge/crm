from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserSession(models.Model):
    """
    Информация о сессии пользователя.
    Отслеживает активные сеансы пользователей.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('Пользователь')
    )

    session_key = models.CharField(
        _('Ключ сессии/токена'),
        max_length=100,
        unique=True
    )

    ip_address = models.GenericIPAddressField(
        _('IP-адрес'),
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        _('Информация о браузере'),
        blank=True
    )

    device_type = models.CharField(
        _('Тип устройства'),
        max_length=20,
        choices=[
            ('desktop', _('Компьютер')),
            ('tablet', _('Планшет')),
            ('mobile', _('Телефон')),
            ('other', _('Другое'))
        ],
        default='other'
    )

    location = models.CharField(
        _('Примерное местоположение'),
        max_length=255,
        blank=True
    )

    started_at = models.DateTimeField(
        _('Время начала сессии'),
        auto_now_add=True
    )

    last_activity = models.DateTimeField(
        _('Время последней активности'),
        auto_now=True
    )

    ended_at = models.DateTimeField(
        _('Время завершения сессии'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('сессия пользователя')
        verbose_name_plural = _('сессии пользователей')
        ordering = ['-started_at']

    def __str__(self):
        return f'Сессия {self.user.username} ({self.started_at})'

    def is_active(self):
        """
        Проверяет, активна ли сессия
        """
        return self.ended_at is None

    def end_session(self):
        """
        Завершает сессию пользователя
        """
        from django.utils import timezone
        if self.is_active():
            self.ended_at = timezone.now()
            self.save(update_fields=['ended_at'])

    @classmethod
    def get_active_sessions(cls, user):
        """
        Возвращает активные сессии пользователя
        """
        return cls.objects.filter(user=user, ended_at=None)


class LoginAttempt(models.Model):
    """
    Модель для отслеживания попыток входа в систему.
    Помогает обнаруживать подозрительную активность.
    """
    username = models.CharField(
        _('Использованное имя пользователя'),
        max_length=150
    )

    ip_address = models.GenericIPAddressField(
        _('IP-адрес'),
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        _('Информация о браузере'),
        blank=True
    )

    timestamp = models.DateTimeField(
        _('Время попытки'),
        auto_now_add=True
    )

    was_successful = models.BooleanField(
        _('Успешность попытки')
    )

    failure_reason = models.CharField(
        _('Причина неудачи'),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _('попытка входа')
        verbose_name_plural = _('попытки входа')
        ordering = ['-timestamp']

    def __str__(self):
        status = 'успешна' if self.was_successful else 'не успешна'
        return f'Попытка входа {self.username} ({self.timestamp}) - {status}'

    @classmethod
    def log_login_attempt(cls, username, ip_address, user_agent, was_successful, failure_reason=''):
        """
        Создает запись о попытке входа
        """
        return cls.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            was_successful=was_successful,
            failure_reason=failure_reason
        )


class UserActivity(models.Model):
    """
    Журнал активности пользователей.
    Отслеживает все действия пользователей в системе.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('Пользователь')
    )

    session = models.ForeignKey(
        'UserSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name=_('Сессия')
    )

    activity_type = models.CharField(
        _('Тип активности'),
        max_length=50,
        choices=[
            ('login', _('Вход в систему')),
            ('logout', _('Выход из системы')),
            ('view', _('Просмотр')),
            ('create', _('Создание')),
            ('update', _('Обновление')),
            ('delete', _('Удаление')),
            ('export', _('Экспорт данных')),
            ('import', _('Импорт данных')),
            ('api', _('API запрос')),
            ('other', _('Другое'))
        ]
    )

    description = models.TextField(
        _('Описание действия')
    )

    timestamp = models.DateTimeField(
        _('Время действия'),
        auto_now_add=True
    )

    ip_address = models.GenericIPAddressField(
        _('IP-адрес'),
        null=True,
        blank=True
    )

    object_type = models.CharField(
        _('Тип объекта'),
        max_length=100,
        blank=True,
        help_text=_('Тип объекта, с которым работали')
    )

    object_id = models.CharField(
        _('ID объекта'),
        max_length=100,
        blank=True,
        help_text=_('Идентификатор объекта, с которым работали')
    )

    class Meta:
        verbose_name = _('активность пользователя')
        verbose_name_plural = _('активности пользователей')
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.username}: {self.activity_type} - {self.timestamp}'

    @classmethod
    def log_activity(cls, user, activity_type, description, session=None, ip_address=None,
                     object_type='', object_id=''):
        """
        Создает запись об активности пользователя
        """
        return cls.objects.create(
            user=user,
            session=session,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            object_type=object_type,
            object_id=object_id
        )
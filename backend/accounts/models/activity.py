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
        verbose_name='Пользователь'
    )

    session_key = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Ключ сессии'
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP адрес'
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )

    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('other', 'Other')
        ],
        default='other',
        verbose_name='Тип устройства'
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Местоположение'
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время начала'
    )

    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Последняя активность'
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время завершения'
    )

    class Meta:
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        ordering = ['-last_activity']

    def __str__(self):
        return f"Сессия {self.user.username} ({self.started_at})"

    def end_session(self):
        """
        Завершает текущую сессию.
        """
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.save()

    def is_active(self):
        """
        Проверяет, активна ли сессия.
        """
        return self.ended_at is None

    def update_activity(self):
        """
        Обновляет время последней активности.
        """
        self.last_activity = timezone.now()
        self.save()

    def get_device_info(self):
        """
        Возвращает информацию об устройстве.
        """
        return {
            'device_type': self.device_type,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'location': self.location
        }

    def get_session_duration(self):
        """
        Возвращает длительность сессии.
        """
        end_time = self.ended_at or timezone.now()
        return end_time - self.started_at

    @classmethod
    def get_active_sessions(cls, user):
        """
        Возвращает все активные сессии пользователя.
        """
        return cls.objects.filter(user=user, ended_at__isnull=True)

    @classmethod
    def end_all_user_sessions(cls, user):
        """
        Завершает все активные сессии пользователя.
        """
        now = timezone.now()
        cls.objects.filter(user=user, ended_at__isnull=True).update(ended_at=now)

    @classmethod
    def get_last_active_session(cls, user):
        """
        Возвращает последнюю активную сессию пользователя.
        """
        return cls.objects.filter(user=user, ended_at__isnull=True).order_by('-last_activity').first()


class LoginAttempt(models.Model):
    """
    Модель для хранения информации о попытках входа.
    """
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        status = 'успешная' if self.was_successful else 'неудачная'
        return f"{status} попытка входа для {self.username} ({self.timestamp})"

    @classmethod
    def log_login_attempt(cls, username, ip_address=None, user_agent=None, was_successful=False, failure_reason=''):
        """
        Логирует попытку входа в систему.
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
    Модель для хранения информации об активности пользователей.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True)
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} ({self.timestamp})"

    @classmethod
    def log_activity(cls, user, activity_type, description, session=None, ip_address=None, object_type='', object_id=''):
        """
        Логирует активность пользователя.
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
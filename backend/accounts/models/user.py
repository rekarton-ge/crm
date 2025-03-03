from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import datetime


class User(AbstractUser):
    """
    Расширенная модель пользователя с дополнительными полями и функциональностью.
    Наследуется от AbstractUser Django.
    """
    phone_number = models.CharField(
        _('Номер телефона'),
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    # Переопределяем поля даты регистрации и последнего входа
    date_joined = models.DateTimeField(_('Дата регистрации'), auto_now_add=True)
    last_login = models.DateTimeField(_('Время последнего входа'), null=True, blank=True)

    # Поля статуса пользователя
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Определяет, может ли пользователь входить в систему. '
                    'Используйте это поле вместо удаления учетных записей.')
    )
    is_staff = models.BooleanField(
        _('Статус сотрудника'),
        default=False,
        help_text=_('Определяет, может ли пользователь входить в панель администратора.')
    )
    is_superuser = models.BooleanField(
        _('Статус суперпользователя'),
        default=False,
        help_text=_('Определяет, что пользователь имеет все разрешения без их явного назначения.')
    )

    # Поля для контроля безопасности и блокировки аккаунта
    failed_login_attempts = models.PositiveIntegerField(_('Счетчик неудачных попыток входа'), default=0)
    last_failed_login = models.DateTimeField(_('Время последней неудачной попытки входа'), null=True, blank=True)
    account_locked_until = models.DateTimeField(_('Время блокировки аккаунта'), null=True, blank=True)

    # Отношение к ролям (будет настроено в models/role.py через ManyToManyField)

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

    def get_full_name(self):
        """
        Возвращает полное имя пользователя.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """
        Возвращает короткое имя пользователя.
        """
        return self.first_name

    def has_role(self, role_name):
        """
        Проверяет, имеет ли пользователь указанную роль.
        """
        return self.roles.filter(name=role_name).exists()

    def has_permission(self, permission_codename):
        """
        Проверяет, имеет ли пользователь указанное разрешение через роли.
        """
        return self.roles.filter(permissions__codename=permission_codename).exists()

    def lock_account(self, duration=None):
        """
        Блокирует аккаунт пользователя на указанное время.
        """
        if duration is None:
            # Стандартная длительность блокировки - 30 минут
            duration = datetime.timedelta(minutes=30)

        self.account_locked_until = timezone.now() + duration
        self.save(update_fields=['account_locked_until'])

    def unlock_account(self):
        """
        Разблокирует аккаунт пользователя.
        """
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])

    def is_locked(self):
        """
        Проверяет, заблокирован ли аккаунт пользователя.
        """
        if not self.account_locked_until:
            return False
        return self.account_locked_until > timezone.now()

    def increment_failed_login_attempts(self):
        """
        Увеличивает счетчик неудачных попыток входа и блокирует аккаунт, если превышен порог.
        """
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()

        # Если превышен порог неудачных попыток (например, 5), блокируем аккаунт
        if self.failed_login_attempts >= 5:
            self.lock_account()
        else:
            self.save(update_fields=['failed_login_attempts', 'last_failed_login'])

    def reset_failed_login_attempts(self):
        """
        Сбрасывает счетчик неудачных попыток входа.
        """
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
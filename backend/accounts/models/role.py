from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """
    Модель роли пользователя в системе.
    Роль определяет набор разрешений, которыми обладает пользователь.
    """
    name = models.CharField(
        _('Название роли'),
        max_length=100,
        unique=True
    )

    description = models.TextField(
        _('Описание роли'),
        blank=True
    )

    is_system = models.BooleanField(
        _('Признак системной роли'),
        default=False,
        help_text=_('Если установлено, то роль является системной и не может быть удалена')
    )

    permissions = models.ManyToManyField(
        'accounts.CustomPermission',
        verbose_name=_('Разрешения'),
        blank=True,
        related_name='roles',
        help_text=_('Разрешения, предоставляемые пользователям с этой ролью')
    )

    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )

    # Связь с пользователями через RoleAssignment
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='RoleAssignment',
        related_name='roles',
        verbose_name=_('Пользователи')
    )

    class Meta:
        verbose_name = _('роль')
        verbose_name_plural = _('роли')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_permissions_list(self):
        """
        Возвращает список кодовых имен разрешений для этой роли
        """
        return list(self.permissions.values_list('codename', flat=True))

    def add_permission(self, permission):
        """
        Добавляет разрешение к роли
        """
        if not self.permissions.filter(pk=permission.pk).exists():
            self.permissions.add(permission)

    def remove_permission(self, permission):
        """
        Удаляет разрешение из роли
        """
        self.permissions.remove(permission)


class RoleAssignment(models.Model):
    """
    Модель для связи между пользователем и ролью.
    Позволяет отслеживать, кто и когда назначил роль,
    а также устанавливать срок действия роли.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_assignments',
        verbose_name=_('Пользователь')
    )

    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='role_assignments',
        verbose_name=_('Роль')
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name=_('Кто назначил')
    )

    assigned_at = models.DateTimeField(
        _('Дата назначения'),
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        _('Срок действия'),
        null=True,
        blank=True,
        help_text=_('Если установлено, то роль будет автоматически отозвана по истечении срока')
    )

    class Meta:
        verbose_name = _('назначение роли')
        verbose_name_plural = _('назначения ролей')
        unique_together = ('user', 'role')
        ordering = ['user', 'role']

    def __str__(self):
        return f'{self.user.username} - {self.role.name}'

    def is_expired(self):
        """
        Проверяет, истек ли срок действия назначения роли
        """
        from django.utils import timezone
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()
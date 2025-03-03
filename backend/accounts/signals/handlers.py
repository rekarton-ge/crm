from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Profile, RoleAssignment, UserActivity

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Создает профиль при создании пользователя.
    """
    if created:
        Profile.objects.create(user=instance)

        # Логируем создание пользователя
        UserActivity.objects.create(
            user=instance,
            activity_type='create',
            description=f'Создание учетной записи пользователя {instance.username}',
            timestamp=timezone.now()
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Сохраняет профиль при обновлении пользователя.
    """
    if hasattr(instance, 'profile') and instance.profile:
        instance.profile.save()


@receiver(post_save, sender=RoleAssignment)
def log_role_assignment(sender, instance, created, **kwargs):
    """
    Логирует назначение роли пользователю.
    """
    if created:
        action_user = instance.assigned_by or instance.user

        UserActivity.objects.create(
            user=action_user,
            activity_type='update',
            description=(
                f'Роль "{instance.role.name}" назначена пользователю {instance.user.username}'
                if instance.assigned_by else
                f'Пользователь получил роль "{instance.role.name}"'
            ),
            object_type='accounts.roleassignment',
            object_id=str(instance.id),
            timestamp=timezone.now()
        )


@receiver(post_delete, sender=RoleAssignment)
def log_role_removal(sender, instance, **kwargs):
    """
    Логирует отзыв роли у пользователя.
    """
    # Получаем пользователя из запроса
    # В сигнале post_delete нет информации о том, кто выполнил удаление
    # Поэтому используем самого пользователя, у которого отозвана роль

    UserActivity.objects.create(
        user=instance.user,
        activity_type='update',
        description=f'Роль "{instance.role.name}" отозвана у пользователя {instance.user.username}',
        object_type='accounts.roleassignment',
        object_id=str(instance.id),
        timestamp=timezone.now()
    )


# Если в settings определена функция для очистки устаревших токенов
if hasattr(settings, 'AUTH_TOKEN_CLEANUP_SCHEDULE'):
    from django.db.models.signals import request_finished


    @receiver(request_finished)
    def cleanup_expired_tokens(**kwargs):
        """
        Очищает устаревшие токены и сессии по завершении запроса,
        если это включено в настройках.
        """
        # Проверяем, нужно ли запускать очистку
        # Например, каждый N-й запрос или по времени

        # Проверка и очистка токенов будет реализована в соответствии
        # с настройками проекта
        pass
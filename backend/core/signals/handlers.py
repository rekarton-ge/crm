"""
Обработчики сигналов.

Этот модуль содержит обработчики сигналов для приложения Django.
"""

import logging
from typing import Any, Dict, Optional, Type, Union

from django.contrib.auth import get_user_model
from django.db.models import Model
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from core.models import (
    Tag, TaggedItem, Setting, Category, AuditLog, LoginAttempt,
    TemplateCategory, Template, TemplateVersion, NotificationChannel,
    NotificationType, Notification, UserNotificationPreference,
    SystemSetting, UserSetting, Theme, TagGroup
)


logger = logging.getLogger('signals')
User = get_user_model()


@receiver(post_save, sender=User)
def handle_user_created(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала создания пользователя.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if created:
        logger.info(f"Пользователь {instance.username} создан")
        
        # Создаем настройки пользователя по умолчанию
        UserSetting.objects.create(
            user=instance,
            key="default_settings",
            value={}  # Пустой JSON объект как значение по умолчанию
        )
        
        # Создаем настройки уведомлений пользователя по умолчанию
        notification_types = NotificationType.objects.all()
        for notification_type in notification_types:
            UserNotificationPreference.objects.create(
                user=instance,
                notification_type=notification_type,
                enabled=notification_type.default_enabled
            )
        
        # Получаем ContentType для модели User
        content_type = ContentType.objects.get_for_model(sender)
        
        # Логируем действие
        AuditLog.objects.create(
            action='user_created',
            user=None,  # Может быть создан администратором или системой
            object_id=instance.pk,
            content_type=content_type,
            data={'username': instance.username, 'email': instance.email}
        )


@receiver(post_save, sender=User)
def handle_user_updated(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала обновления пользователя.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if not created:
        logger.info(f"Пользователь {instance.username} обновлен")
        
        # Получаем ContentType для модели User
        content_type = ContentType.objects.get_for_model(sender)
        
        # Логируем действие
        AuditLog.objects.create(
            action='user_updated',
            user=instance,  # Пользователь мог обновить сам себя
            object_id=instance.pk,
            content_type=content_type,
            data={'username': instance.username, 'email': instance.email}
        )


@receiver(post_delete, sender=User)
def handle_user_deleted(sender: Type[Model], instance: Model, **kwargs: Any) -> None:
    """
    Обработчик сигнала удаления пользователя.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        **kwargs: Дополнительные аргументы.
    """
    logger.info(f"Пользователь {instance.username} удален")
    
    # Получаем ContentType для модели User
    content_type = ContentType.objects.get_for_model(sender)
    
    # Логируем действие
    AuditLog.objects.create(
        action='user_deleted',
        user=None,  # Пользователь уже удален
        object_id=instance.pk,
        content_type=content_type,
        data={'username': instance.username, 'email': instance.email}
    )


@receiver(post_save, sender=Tag)
def handle_tag_created(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала создания тега.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if created:
        logger.info(f"Тег {instance.name} создан")
        
        # Получаем ContentType для модели Tag
        content_type = ContentType.objects.get_for_model(sender)
        
        # Логируем действие
        AuditLog.objects.create(
            action='tag_created',
            user=None,  # Может быть создан системой
            object_id=instance.pk,
            content_type=content_type,
            data={'name': instance.name, 'slug': instance.slug}
        )


@receiver(post_save, sender=Tag)
def handle_tag_updated(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала post_save для модели Tag.

    Вызывается при обновлении тега.
    """
    if not created:
        logger.info(f"Тег {instance.name} обновлен")
        
        # Логируем действие
        AuditLog.objects.create(
            action='tag_updated',
            user=None,  # Может быть обновлен системой
            object_id=instance.pk,
            content_type=ContentType.objects.get_for_model(instance.__class__),
            data={'name': instance.name, 'slug': instance.slug}
        )


@receiver(post_delete, sender=Tag)
def handle_tag_deleted(sender: Type[Model], instance: Model, **kwargs: Any) -> None:
    """
    Обработчик сигнала post_delete для модели Tag.

    Вызывается при удалении тега.
    """
    logger.info(f"Тег {instance.name} удален")
    
    # Логируем действие
    AuditLog.objects.create(
        action='tag_deleted',
        user=None,  # Может быть удален системой
        object_id=instance.pk,
        content_type=ContentType.objects.get_for_model(sender),
        data={'name': instance.name, 'slug': instance.slug}
    )


@receiver(post_save, sender=Notification)
def handle_notification_created(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала создания уведомления.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if created:
        logger.info(f"Уведомление {instance.pk} создано для пользователя {instance.user.username}")
        
        # Отправляем уведомление через соответствующие каналы
        for channel in instance.notification_type.channels.all():
            try:
                # Здесь должна быть логика отправки уведомления через канал
                # Например, отправка email, push-уведомления и т.д.
                pass
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления через канал {channel.name}: {str(e)}")


@receiver(post_save, sender=Notification)
def handle_notification_read(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала прочтения уведомления.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if not created and instance.read_at is not None:
        logger.info(f"Уведомление {instance.pk} прочитано пользователем {instance.user.username}")


@receiver(post_save, sender=Template)
def handle_template_created(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала создания шаблона.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if created:
        logger.info(f"Шаблон {instance.name} создан")
        
        # Создаем первую версию шаблона
        TemplateVersion.objects.create(
            template=instance,
            content=instance.content,
            version=1,
            is_active=True
        )
        
        # Получаем ContentType для модели Template
        content_type = ContentType.objects.get_for_model(sender)
        
        # Логируем действие
        AuditLog.objects.create(
            action='template_created',
            user=None,  # Может быть создан системой
            object_id=instance.pk,
            content_type=content_type,
            data={'name': instance.name}
        )


@receiver(post_save, sender=Template)
def handle_template_updated(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала обновления шаблона.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    if not created:
        logger.info(f"Шаблон {instance.name} обновлен")
        
        # Получаем последнюю версию шаблона
        last_version = TemplateVersion.objects.filter(template=instance).order_by('-version').first()
        
        # Если содержимое изменилось, создаем новую версию
        if last_version and last_version.content != instance.content:
            TemplateVersion.objects.create(
                template=instance,
                content=instance.content,
                version=last_version.version + 1,
                is_active=True
            )
            
            # Деактивируем предыдущую версию
            last_version.is_active = False
            last_version.save()
        
        # Логируем действие
        AuditLog.objects.create(
            action='template_updated',
            user=None,  # Может быть обновлен системой
            object_id=instance.pk,
            content_type=instance._meta.model,
            data={'name': instance.name}
        )


@receiver(post_delete, sender=Template)
def handle_template_deleted(sender: Type[Model], instance: Model, **kwargs: Any) -> None:
    """
    Обработчик сигнала удаления шаблона.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        **kwargs: Дополнительные аргументы.
    """
    logger.info(f"Шаблон {instance.name} удален")
    
    # Логируем действие
    AuditLog.objects.create(
        action='template_deleted',
        user=None,  # Может быть удален системой
        object_id=instance.pk,
        content_type=instance._meta.model,
        data={'name': instance.name}
    )


@receiver(post_save, sender=SystemSetting)
@receiver(post_save, sender=UserSetting)
def handle_setting_changed(sender: Type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    """
    Обработчик сигнала изменения настройки.
    
    Args:
        sender (Type[Model]): Модель, отправившая сигнал.
        instance (Model): Экземпляр модели.
        created (bool): Флаг, указывающий, что объект был создан.
        **kwargs: Дополнительные аргументы.
    """
    action = 'setting_created' if created else 'setting_updated'
    setting_type = 'system' if sender == SystemSetting else 'user'
    
    logger.info(f"{setting_type.capitalize()} настройка {instance.key} {'создана' if created else 'обновлена'}")
    
    # Получаем ContentType для модели
    content_type = ContentType.objects.get_for_model(sender)
    
    # Логируем действие
    AuditLog.objects.create(
        action=action,
        user=getattr(instance, 'user', None),  # Для UserSetting
        object_id=instance.pk,
        content_type=content_type,
        data={'key': instance.key, 'value': str(instance.value), 'type': setting_type}
    )

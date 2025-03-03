"""
Web-уведомления.

Этот модуль содержит классы для работы с web-уведомлениями.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.notifications.base import BaseNotification, NotificationChannel, NotificationTemplate


logger = logging.getLogger('notifications.web')


class WebNotification(BaseNotification):
    """
    Класс для web-уведомлений.
    
    Web-уведомление содержит дополнительные параметры для отображения в веб-интерфейсе.
    """
    
    def __init__(
        self,
        recipient,
        subject: str,
        body: str,
        template: Optional[NotificationTemplate] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channel: Optional[NotificationChannel] = None,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        link: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Инициализация web-уведомления.
        
        Args:
            recipient: Получатель уведомления.
            subject (str): Заголовок уведомления.
            body (str): Содержимое уведомления.
            template (NotificationTemplate, optional): Шаблон уведомления.
            context (Dict[str, Any], optional): Контекст шаблона.
            metadata (Dict[str, Any], optional): Метаданные уведомления.
            channel (NotificationChannel, optional): Канал отправки уведомления.
            icon (str, optional): URL иконки уведомления.
            image (str, optional): URL изображения уведомления.
            link (str, optional): URL для перехода при клике на уведомление.
            category (str, optional): Категория уведомления.
            priority (str, optional): Приоритет уведомления.
            actions (List[Dict[str, Any]], optional): Список действий для уведомления.
        """
        super().__init__(
            recipient=recipient,
            subject=subject,
            body=body,
            template=template,
            context=context,
            metadata=metadata,
            channel=channel
        )
        
        self.icon = icon
        self.image = image
        self.link = link
        self.category = category or 'info'
        self.priority = priority or 'normal'
        self.actions = actions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует уведомление в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с информацией об уведомлении.
        """
        data = super().to_dict()
        data.update({
            'icon': self.icon,
            'image': self.image,
            'link': self.link,
            'category': self.category,
            'priority': self.priority,
            'actions': self.actions,
        })
        return data
    
    def to_json(self) -> str:
        """
        Преобразует уведомление в JSON.
        
        Returns:
            str: JSON-представление уведомления.
        """
        return json.dumps(self.to_dict())


class WebNotificationChannel(NotificationChannel):
    """
    Канал отправки web-уведомлений.
    
    Сохраняет уведомления в базе данных для отображения в веб-интерфейсе.
    """
    
    def __init__(self, notification_model=None):
        """
        Инициализация канала отправки web-уведомлений.
        
        Args:
            notification_model: Модель для сохранения уведомлений.
        """
        from core.models import Notification
        self.notification_model = notification_model or Notification
    
    def get_channel_name(self) -> str:
        """
        Возвращает имя канала.
        
        Returns:
            str: Имя канала.
        """
        return 'web'
    
    def send(self, notification: WebNotification) -> bool:
        """
        Отправляет web-уведомление.
        
        Args:
            notification (WebNotification): Уведомление для отправки.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        try:
            # Сохраняем уведомление в базе данных
            with transaction.atomic():
                db_notification = self.notification_model(
                    user=notification.recipient,
                    title=notification.subject,
                    message=notification.body,
                    icon=notification.icon,
                    image=notification.image,
                    link=notification.link,
                    category=notification.category,
                    priority=notification.priority,
                    actions=notification.actions,
                    metadata=notification.metadata,
                    created_at=notification.created_at,
                    is_read=False
                )
                db_notification.save()
            
            # Обновляем уведомление
            notification.is_sent = True
            notification.sent_at = timezone.now()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки web-уведомления: {str(e)}")
            return False
    
    def send_bulk(self, notifications: List[WebNotification]) -> Dict[int, bool]:
        """
        Отправляет несколько web-уведомлений.
        
        Args:
            notifications (List[WebNotification]): Список уведомлений для отправки.
        
        Returns:
            Dict[int, bool]: Словарь с идентификаторами уведомлений и результатами отправки.
        """
        results = {}
        
        try:
            # Сохраняем уведомления в базе данных
            with transaction.atomic():
                for i, notification in enumerate(notifications):
                    try:
                        db_notification = self.notification_model(
                            user=notification.recipient,
                            title=notification.subject,
                            message=notification.body,
                            icon=notification.icon,
                            image=notification.image,
                            link=notification.link,
                            category=notification.category,
                            priority=notification.priority,
                            actions=notification.actions,
                            metadata=notification.metadata,
                            created_at=notification.created_at,
                            is_read=False
                        )
                        db_notification.save()
                        
                        # Обновляем уведомление
                        notification.is_sent = True
                        notification.sent_at = timezone.now()
                        
                        results[i] = True
                    except Exception as e:
                        logger.error(f"Ошибка отправки web-уведомления: {str(e)}")
                        results[i] = False
        except Exception as e:
            logger.error(f"Ошибка отправки web-уведомлений: {str(e)}")
            
            # Если произошла ошибка транзакции, все уведомления не отправлены
            for i in range(len(notifications)):
                if i not in results:
                    results[i] = False
        
        return results
    
    def mark_as_read(self, notification_id: int) -> bool:
        """
        Отмечает уведомление как прочитанное.
        
        Args:
            notification_id (int): Идентификатор уведомления.
        
        Returns:
            bool: True, если уведомление успешно отмечено как прочитанное, иначе False.
        """
        try:
            # Получаем уведомление из базы данных
            db_notification = self.notification_model.objects.get(pk=notification_id)
            
            # Отмечаем уведомление как прочитанное
            db_notification.is_read = True
            db_notification.read_at = timezone.now()
            db_notification.save(update_fields=['is_read', 'read_at'])
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отметки уведомления как прочитанного: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """
        Отмечает все уведомления пользователя как прочитанные.
        
        Args:
            user_id (int): Идентификатор пользователя.
        
        Returns:
            bool: True, если уведомления успешно отмечены как прочитанные, иначе False.
        """
        try:
            # Получаем все непрочитанные уведомления пользователя
            db_notifications = self.notification_model.objects.filter(
                user_id=user_id,
                is_read=False
            )
            
            # Отмечаем уведомления как прочитанные
            now = timezone.now()
            db_notifications.update(is_read=True, read_at=now)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отметки всех уведомлений как прочитанных: {str(e)}")
            return False
    
    def delete_notification(self, notification_id: int) -> bool:
        """
        Удаляет уведомление.
        
        Args:
            notification_id (int): Идентификатор уведомления.
        
        Returns:
            bool: True, если уведомление успешно удалено, иначе False.
        """
        try:
            # Получаем уведомление из базы данных
            db_notification = self.notification_model.objects.get(pk=notification_id)
            
            # Удаляем уведомление
            db_notification.delete()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления уведомления: {str(e)}")
            return False
    
    def delete_all_notifications(self, user_id: int) -> bool:
        """
        Удаляет все уведомления пользователя.
        
        Args:
            user_id (int): Идентификатор пользователя.
        
        Returns:
            bool: True, если уведомления успешно удалены, иначе False.
        """
        try:
            # Получаем все уведомления пользователя
            db_notifications = self.notification_model.objects.filter(user_id=user_id)
            
            # Удаляем уведомления
            db_notifications.delete()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления всех уведомлений: {str(e)}")
            return False

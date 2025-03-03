"""
Push-уведомления.

Этот модуль содержит классы для работы с push-уведомлениями.
"""

import json
import logging
import requests
from typing import Any, Dict, List, Optional, Union

from django.conf import settings

from core.notifications.base import BaseNotification, NotificationChannel, NotificationTemplate


logger = logging.getLogger('notifications.push')


class PushNotification(BaseNotification):
    """
    Класс для push-уведомлений.
    
    Push-уведомление содержит дополнительные параметры для отправки push-уведомлений.
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
        badge: Optional[int] = None,
        sound: Optional[str] = None,
        click_action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        priority: Optional[str] = None
    ):
        """
        Инициализация push-уведомления.
        
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
            badge (int, optional): Значок уведомления.
            sound (str, optional): Звук уведомления.
            click_action (str, optional): Действие при клике на уведомление.
            data (Dict[str, Any], optional): Дополнительные данные уведомления.
            ttl (int, optional): Время жизни уведомления в секундах.
            priority (str, optional): Приоритет уведомления.
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
        self.badge = badge
        self.sound = sound or 'default'
        self.click_action = click_action
        self.data = data or {}
        self.ttl = ttl or 2419200  # 4 недели по умолчанию
        self.priority = priority or 'high'
    
    def get_recipient_token(self) -> str:
        """
        Возвращает токен получателя.
        
        Returns:
            str: Токен получателя.
        """
        if hasattr(self.recipient, 'push_token'):
            return self.recipient.push_token
        
        if hasattr(self.recipient, 'device') and hasattr(self.recipient.device, 'push_token'):
            return self.recipient.device.push_token
        
        return str(self.recipient)
    
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
            'badge': self.badge,
            'sound': self.sound,
            'click_action': self.click_action,
            'data': self.data,
            'ttl': self.ttl,
            'priority': self.priority,
        })
        return data
    
    def to_fcm_payload(self) -> Dict[str, Any]:
        """
        Преобразует уведомление в payload для Firebase Cloud Messaging.
        
        Returns:
            Dict[str, Any]: Payload для FCM.
        """
        payload = {
            'notification': {
                'title': self.subject,
                'body': self.body,
            },
            'data': self.data,
            'android': {
                'priority': self.priority,
                'ttl': f"{self.ttl}s",
                'notification': {
                    'sound': self.sound,
                    'click_action': self.click_action,
                }
            },
            'apns': {
                'payload': {
                    'aps': {
                        'sound': self.sound,
                        'badge': self.badge,
                    }
                }
            },
            'webpush': {
                'notification': {
                    'icon': self.icon,
                    'image': self.image,
                }
            }
        }
        
        # Удаляем None значения
        for key in list(payload['notification'].keys()):
            if payload['notification'][key] is None:
                del payload['notification'][key]
        
        for key in list(payload['android']['notification'].keys()):
            if payload['android']['notification'][key] is None:
                del payload['android']['notification'][key]
        
        for key in list(payload['apns']['payload']['aps'].keys()):
            if payload['apns']['payload']['aps'][key] is None:
                del payload['apns']['payload']['aps'][key]
        
        for key in list(payload['webpush']['notification'].keys()):
            if payload['webpush']['notification'][key] is None:
                del payload['webpush']['notification'][key]
        
        return payload


class PushNotificationChannel(NotificationChannel):
    """
    Канал отправки push-уведомлений.
    
    Отправляет уведомления через Firebase Cloud Messaging.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        fcm_url: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Инициализация канала отправки push-уведомлений.
        
        Args:
            api_key (str, optional): API ключ Firebase Cloud Messaging.
            fcm_url (str, optional): URL Firebase Cloud Messaging.
            timeout (int, optional): Таймаут запроса в секундах.
        """
        self.api_key = api_key or getattr(settings, 'FCM_API_KEY', '')
        self.fcm_url = fcm_url or getattr(settings, 'FCM_URL', 'https://fcm.googleapis.com/fcm/send')
        self.timeout = timeout
    
    def get_channel_name(self) -> str:
        """
        Возвращает имя канала.
        
        Returns:
            str: Имя канала.
        """
        return 'push'
    
    def send(self, notification: PushNotification) -> bool:
        """
        Отправляет push-уведомление.
        
        Args:
            notification (PushNotification): Уведомление для отправки.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        try:
            # Получаем токен получателя
            token = notification.get_recipient_token()
            
            if not token:
                logger.error("Не удалось получить токен получателя")
                return False
            
            # Создаем payload
            payload = notification.to_fcm_payload()
            payload['to'] = token
            
            # Отправляем запрос
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'key={self.api_key}'
            }
            
            response = requests.post(
                self.fcm_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            
            # Проверяем ответ
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('success', 0) > 0:
                    return True
                
                logger.error(f"Ошибка отправки push-уведомления: {response_data}")
                return False
            
            logger.error(f"Ошибка отправки push-уведомления: {response.status_code} {response.text}")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки push-уведомления: {str(e)}")
            return False
    
    def send_bulk(self, notifications: List[PushNotification]) -> Dict[int, bool]:
        """
        Отправляет несколько push-уведомлений.
        
        Args:
            notifications (List[PushNotification]): Список уведомлений для отправки.
        
        Returns:
            Dict[int, bool]: Словарь с идентификаторами уведомлений и результатами отправки.
        """
        results = {}
        
        # Группируем уведомления по токенам
        token_notifications = {}
        for i, notification in enumerate(notifications):
            token = notification.get_recipient_token()
            
            if not token:
                results[i] = False
                continue
            
            if token not in token_notifications:
                token_notifications[token] = []
            
            token_notifications[token].append((i, notification))
        
        # Отправляем уведомления по группам
        for token, token_notifs in token_notifications.items():
            # Если в группе только одно уведомление, отправляем его напрямую
            if len(token_notifs) == 1:
                i, notification = token_notifs[0]
                results[i] = self.send(notification)
                continue
            
            # Если в группе несколько уведомлений, отправляем их в одном запросе
            try:
                # Создаем payload для multicast
                registration_ids = [token]
                
                # Используем первое уведомление в группе
                _, notification = token_notifs[0]
                payload = notification.to_fcm_payload()
                payload['registration_ids'] = registration_ids
                
                # Отправляем запрос
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'key={self.api_key}'
                }
                
                response = requests.post(
                    self.fcm_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=self.timeout
                )
                
                # Проверяем ответ
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if response_data.get('success', 0) > 0:
                        for i, _ in token_notifs:
                            results[i] = True
                    else:
                        for i, _ in token_notifs:
                            results[i] = False
                        
                        logger.error(f"Ошибка отправки push-уведомлений: {response_data}")
                else:
                    for i, _ in token_notifs:
                        results[i] = False
                    
                    logger.error(f"Ошибка отправки push-уведомлений: {response.status_code} {response.text}")
            except Exception as e:
                for i, _ in token_notifs:
                    results[i] = False
                
                logger.error(f"Ошибка отправки push-уведомлений: {str(e)}")
        
        return results

"""
Базовые классы для уведомлений.

Этот модуль содержит базовые классы для работы с уведомлениями.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.template import Context, Template
from django.utils import timezone

from core.templates_engine.parsers import TemplateParser
from core.templates_engine.variables import VariableRegistry


logger = logging.getLogger('notifications')
User = get_user_model()


class NotificationTemplate:
    """
    Класс для работы с шаблонами уведомлений.
    
    Шаблон уведомления содержит заголовок, содержимое и другие параметры.
    """
    
    def __init__(
        self,
        subject_template: str,
        body_template: str,
        template_parser: Optional[TemplateParser] = None,
        variable_registry: Optional[VariableRegistry] = None
    ):
        """
        Инициализация шаблона уведомления.
        
        Args:
            subject_template (str): Шаблон заголовка.
            body_template (str): Шаблон содержимого.
            template_parser (TemplateParser, optional): Парсер шаблонов.
            variable_registry (VariableRegistry, optional): Реестр переменных.
        """
        self.subject_template = subject_template
        self.body_template = body_template
        self.template_parser = template_parser or TemplateParser()
        self.variable_registry = variable_registry or VariableRegistry()
    
    def render_subject(self, context: Dict[str, Any]) -> str:
        """
        Рендерит заголовок уведомления.
        
        Args:
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренный заголовок.
        """
        # Создаем шаблон Django
        template = Template(self.subject_template)
        
        # Создаем контекст Django
        django_context = Context(context)
        
        # Рендерим шаблон
        return template.render(django_context)
    
    def render_body(self, context: Dict[str, Any]) -> str:
        """
        Рендерит содержимое уведомления.
        
        Args:
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренное содержимое.
        """
        # Создаем шаблон Django
        template = Template(self.body_template)
        
        # Создаем контекст Django
        django_context = Context(context)
        
        # Рендерим шаблон
        return template.render(django_context)
    
    def validate(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Проверяет контекст шаблона.
        
        Args:
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            Tuple[bool, Dict[str, str]]: Флаг валидности и словарь с ошибками.
        """
        # Проверяем контекст для заголовка
        subject_valid, subject_errors = self.template_parser.validate(self.subject_template, context)
        
        # Проверяем контекст для содержимого
        body_valid, body_errors = self.template_parser.validate(self.body_template, context)
        
        # Объединяем ошибки
        errors = {**subject_errors, **body_errors}
        
        return len(errors) == 0, errors
    
    def get_variables(self) -> Set[str]:
        """
        Возвращает множество переменных, используемых в шаблоне.
        
        Returns:
            Set[str]: Множество переменных.
        """
        # Извлекаем переменные из заголовка
        subject_variables = self.template_parser.variable_parser.parse(self.subject_template)
        
        # Извлекаем переменные из содержимого
        body_variables = self.template_parser.variable_parser.parse(self.body_template)
        
        # Объединяем переменные
        return subject_variables | body_variables


class NotificationChannel(ABC):
    """
    Базовый класс для каналов уведомлений.
    
    Канал уведомлений отвечает за отправку уведомлений через определенный канал связи.
    """
    
    @abstractmethod
    def send(self, notification: 'BaseNotification') -> bool:
        """
        Отправляет уведомление.
        
        Args:
            notification (BaseNotification): Уведомление для отправки.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        pass
    
    @abstractmethod
    def send_bulk(self, notifications: List['BaseNotification']) -> Dict[int, bool]:
        """
        Отправляет несколько уведомлений.
        
        Args:
            notifications (List[BaseNotification]): Список уведомлений для отправки.
        
        Returns:
            Dict[int, bool]: Словарь с идентификаторами уведомлений и результатами отправки.
        """
        pass
    
    @abstractmethod
    def get_channel_name(self) -> str:
        """
        Возвращает имя канала.
        
        Returns:
            str: Имя канала.
        """
        pass


class BaseNotification:
    """
    Базовый класс для уведомлений.
    
    Уведомление содержит информацию о получателе, заголовке, содержимом и других параметрах.
    """
    
    def __init__(
        self,
        recipient: User,
        subject: str,
        body: str,
        template: Optional[NotificationTemplate] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channel: Optional[NotificationChannel] = None
    ):
        """
        Инициализация уведомления.
        
        Args:
            recipient (User): Получатель уведомления.
            subject (str): Заголовок уведомления.
            body (str): Содержимое уведомления.
            template (NotificationTemplate, optional): Шаблон уведомления.
            context (Dict[str, Any], optional): Контекст шаблона.
            metadata (Dict[str, Any], optional): Метаданные уведомления.
            channel (NotificationChannel, optional): Канал отправки уведомления.
        """
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.template = template
        self.context = context or {}
        self.metadata = metadata or {}
        self.channel = channel
        self.created_at = timezone.now()
        self.sent_at = None
        self.read_at = None
        self.is_sent = False
        self.is_read = False
        self.error = None
    
    def send(self) -> bool:
        """
        Отправляет уведомление.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        if not self.channel:
            self.error = "Канал отправки не указан"
            return False
        
        try:
            # Отправляем уведомление через канал
            result = self.channel.send(self)
            
            if result:
                self.is_sent = True
                self.sent_at = timezone.now()
            else:
                self.error = "Ошибка отправки уведомления"
            
            return result
        except Exception as e:
            self.error = str(e)
            logger.error(f"Ошибка отправки уведомления: {str(e)}")
            return False
    
    def mark_as_read(self) -> None:
        """
        Отмечает уведомление как прочитанное.
        """
        self.is_read = True
        self.read_at = timezone.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует уведомление в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с информацией об уведомлении.
        """
        return {
            'recipient': self.recipient.pk,
            'subject': self.subject,
            'body': self.body,
            'created_at': self.created_at,
            'sent_at': self.sent_at,
            'read_at': self.read_at,
            'is_sent': self.is_sent,
            'is_read': self.is_read,
            'metadata': self.metadata,
            'channel': self.channel.get_channel_name() if self.channel else None,
            'error': self.error,
        }


class NotificationManager:
    """
    Менеджер уведомлений.
    
    Отвечает за создание, отправку и управление уведомлениями.
    """
    
    def __init__(self, channels: Optional[List[NotificationChannel]] = None):
        """
        Инициализация менеджера уведомлений.
        
        Args:
            channels (List[NotificationChannel], optional): Список каналов отправки уведомлений.
        """
        self.channels = channels or []
    
    def register_channel(self, channel: NotificationChannel) -> None:
        """
        Регистрирует канал отправки уведомлений.
        
        Args:
            channel (NotificationChannel): Канал отправки уведомлений.
        """
        self.channels.append(channel)
    
    def get_channel(self, channel_name: str) -> Optional[NotificationChannel]:
        """
        Возвращает канал отправки уведомлений по имени.
        
        Args:
            channel_name (str): Имя канала.
        
        Returns:
            Optional[NotificationChannel]: Канал отправки уведомлений или None, если канал не найден.
        """
        for channel in self.channels:
            if channel.get_channel_name() == channel_name:
                return channel
        
        return None
    
    def create_notification(
        self,
        recipient: User,
        subject: str,
        body: str,
        template: Optional[NotificationTemplate] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channel_name: Optional[str] = None
    ) -> BaseNotification:
        """
        Создает уведомление.
        
        Args:
            recipient (User): Получатель уведомления.
            subject (str): Заголовок уведомления.
            body (str): Содержимое уведомления.
            template (NotificationTemplate, optional): Шаблон уведомления.
            context (Dict[str, Any], optional): Контекст шаблона.
            metadata (Dict[str, Any], optional): Метаданные уведомления.
            channel_name (str, optional): Имя канала отправки уведомления.
        
        Returns:
            BaseNotification: Созданное уведомление.
        """
        # Если указан шаблон и контекст, рендерим заголовок и содержимое
        if template and context:
            subject = template.render_subject(context)
            body = template.render_body(context)
        
        # Если указано имя канала, получаем канал
        channel = None
        if channel_name:
            channel = self.get_channel(channel_name)
        
        # Создаем уведомление
        notification = BaseNotification(
            recipient=recipient,
            subject=subject,
            body=body,
            template=template,
            context=context,
            metadata=metadata,
            channel=channel
        )
        
        return notification
    
    def send_notification(self, notification: BaseNotification) -> bool:
        """
        Отправляет уведомление.
        
        Args:
            notification (BaseNotification): Уведомление для отправки.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        return notification.send()
    
    def send_bulk_notifications(self, notifications: List[BaseNotification]) -> Dict[int, bool]:
        """
        Отправляет несколько уведомлений.
        
        Args:
            notifications (List[BaseNotification]): Список уведомлений для отправки.
        
        Returns:
            Dict[int, bool]: Словарь с идентификаторами уведомлений и результатами отправки.
        """
        results = {}
        
        # Группируем уведомления по каналам
        channel_notifications = {}
        for i, notification in enumerate(notifications):
            if not notification.channel:
                results[i] = False
                continue
            
            channel_name = notification.channel.get_channel_name()
            if channel_name not in channel_notifications:
                channel_notifications[channel_name] = []
            
            channel_notifications[channel_name].append((i, notification))
        
        # Отправляем уведомления через соответствующие каналы
        for channel_name, channel_notifs in channel_notifications.items():
            channel = self.get_channel(channel_name)
            if not channel:
                for i, _ in channel_notifs:
                    results[i] = False
                continue
            
            # Извлекаем уведомления
            indices, notifs = zip(*channel_notifs)
            
            # Отправляем уведомления через канал
            channel_results = channel.send_bulk(list(notifs))
            
            # Обновляем результаты
            for i, notification in enumerate(notifs):
                if channel_results.get(i, False):
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    results[indices[i]] = True
                else:
                    notification.error = "Ошибка отправки уведомления"
                    results[indices[i]] = False
        
        return results

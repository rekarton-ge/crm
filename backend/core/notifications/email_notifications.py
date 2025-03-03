"""
Email-уведомления.

Этот модуль содержит классы для работы с email-уведомлениями.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from core.notifications.base import BaseNotification, NotificationChannel, NotificationTemplate


logger = logging.getLogger('notifications.email')


class EmailNotification(BaseNotification):
    """
    Класс для email-уведомлений.
    
    Email-уведомление содержит дополнительные параметры для отправки email.
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
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        html_body: Optional[str] = None
    ):
        """
        Инициализация email-уведомления.
        
        Args:
            recipient: Получатель уведомления.
            subject (str): Заголовок уведомления.
            body (str): Содержимое уведомления.
            template (NotificationTemplate, optional): Шаблон уведомления.
            context (Dict[str, Any], optional): Контекст шаблона.
            metadata (Dict[str, Any], optional): Метаданные уведомления.
            channel (NotificationChannel, optional): Канал отправки уведомления.
            from_email (str, optional): Email отправителя.
            cc (List[str], optional): Список адресов для копии.
            bcc (List[str], optional): Список адресов для скрытой копии.
            reply_to (List[str], optional): Список адресов для ответа.
            attachments (List[Dict[str, Any]], optional): Список вложений.
            html_body (str, optional): HTML-содержимое уведомления.
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
        
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.cc = cc or []
        self.bcc = bcc or []
        self.reply_to = reply_to or []
        self.attachments = attachments or []
        self.html_body = html_body or body
    
    def get_recipient_email(self) -> str:
        """
        Возвращает email получателя.
        
        Returns:
            str: Email получателя.
        """
        if hasattr(self.recipient, 'email'):
            return self.recipient.email
        
        return str(self.recipient)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует уведомление в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с информацией об уведомлении.
        """
        data = super().to_dict()
        data.update({
            'from_email': self.from_email,
            'cc': self.cc,
            'bcc': self.bcc,
            'reply_to': self.reply_to,
            'attachments': self.attachments,
            'html_body': self.html_body,
        })
        return data


class EmailNotificationChannel(NotificationChannel):
    """
    Канал отправки email-уведомлений.
    
    Отправляет уведомления по email.
    """
    
    def __init__(
        self,
        connection=None,
        from_email: Optional[str] = None,
        fail_silently: bool = False,
        html_template: Optional[str] = None,
        text_template: Optional[str] = None
    ):
        """
        Инициализация канала отправки email-уведомлений.
        
        Args:
            connection: Соединение для отправки email.
            from_email (str, optional): Email отправителя по умолчанию.
            fail_silently (bool, optional): Флаг, указывающий, нужно ли подавлять исключения.
            html_template (str, optional): Путь к HTML-шаблону.
            text_template (str, optional): Путь к текстовому шаблону.
        """
        self.connection = connection
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.fail_silently = fail_silently
        self.html_template = html_template
        self.text_template = text_template
    
    def get_channel_name(self) -> str:
        """
        Возвращает имя канала.
        
        Returns:
            str: Имя канала.
        """
        return 'email'
    
    def send(self, notification: EmailNotification) -> bool:
        """
        Отправляет email-уведомление.
        
        Args:
            notification (EmailNotification): Уведомление для отправки.
        
        Returns:
            bool: True, если уведомление успешно отправлено, иначе False.
        """
        try:
            # Получаем email получателя
            to_email = notification.get_recipient_email()
            
            # Создаем email
            if notification.html_body:
                # Создаем email с HTML-содержимым
                email = EmailMultiAlternatives(
                    subject=notification.subject,
                    body=notification.body,
                    from_email=notification.from_email or self.from_email,
                    to=[to_email],
                    cc=notification.cc,
                    bcc=notification.bcc,
                    reply_to=notification.reply_to,
                    connection=self.connection
                )
                email.attach_alternative(notification.html_body, 'text/html')
            else:
                # Создаем обычный email
                email = EmailMessage(
                    subject=notification.subject,
                    body=notification.body,
                    from_email=notification.from_email or self.from_email,
                    to=[to_email],
                    cc=notification.cc,
                    bcc=notification.bcc,
                    reply_to=notification.reply_to,
                    connection=self.connection
                )
            
            # Добавляем вложения
            for attachment in notification.attachments:
                email.attach(
                    filename=attachment.get('filename', ''),
                    content=attachment.get('content', ''),
                    mimetype=attachment.get('mimetype', None)
                )
            
            # Отправляем email
            email.send(fail_silently=self.fail_silently)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки email-уведомления: {str(e)}")
            return False
    
    def send_bulk(self, notifications: List[EmailNotification]) -> Dict[int, bool]:
        """
        Отправляет несколько email-уведомлений.
        
        Args:
            notifications (List[EmailNotification]): Список уведомлений для отправки.
        
        Returns:
            Dict[int, bool]: Словарь с идентификаторами уведомлений и результатами отправки.
        """
        results = {}
        
        # Получаем соединение
        connection = self.connection or get_connection(fail_silently=self.fail_silently)
        
        try:
            # Открываем соединение
            connection.open()
            
            # Отправляем уведомления
            for i, notification in enumerate(notifications):
                try:
                    # Устанавливаем соединение для уведомления
                    notification.channel.connection = connection
                    
                    # Отправляем уведомление
                    results[i] = notification.send()
                except Exception as e:
                    logger.error(f"Ошибка отправки email-уведомления: {str(e)}")
                    results[i] = False
        finally:
            # Закрываем соединение
            connection.close()
        
        return results
    
    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Рендерит шаблон с использованием контекста.
        
        Args:
            template_path (str): Путь к шаблону.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренный шаблон.
        """
        return render_to_string(template_path, context)
    
    def create_email_from_template(
        self,
        subject: str,
        to_email: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        html_template: Optional[str] = None,
        text_template: Optional[str] = None
    ) -> Union[EmailMessage, EmailMultiAlternatives]:
        """
        Создает email из шаблона.
        
        Args:
            subject (str): Заголовок email.
            to_email (str): Email получателя.
            context (Dict[str, Any]): Контекст шаблона.
            from_email (str, optional): Email отправителя.
            cc (List[str], optional): Список адресов для копии.
            bcc (List[str], optional): Список адресов для скрытой копии.
            reply_to (List[str], optional): Список адресов для ответа.
            attachments (List[Dict[str, Any]], optional): Список вложений.
            html_template (str, optional): Путь к HTML-шаблону.
            text_template (str, optional): Путь к текстовому шаблону.
        
        Returns:
            Union[EmailMessage, EmailMultiAlternatives]: Созданный email.
        """
        # Определяем шаблоны
        html_template = html_template or self.html_template
        text_template = text_template or self.text_template
        
        # Рендерим шаблоны
        if html_template:
            html_content = self.render_template(html_template, context)
            
            if text_template:
                text_content = self.render_template(text_template, context)
            else:
                text_content = strip_tags(html_content)
            
            # Создаем email с HTML-содержимым
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email or self.from_email,
                to=[to_email],
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
                connection=self.connection
            )
            email.attach_alternative(html_content, 'text/html')
        else:
            if text_template:
                text_content = self.render_template(text_template, context)
            else:
                text_content = ''
            
            # Создаем обычный email
            email = EmailMessage(
                subject=subject,
                body=text_content,
                from_email=from_email or self.from_email,
                to=[to_email],
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
                connection=self.connection
            )
        
        # Добавляем вложения
        if attachments:
            for attachment in attachments:
                email.attach(
                    filename=attachment.get('filename', ''),
                    content=attachment.get('content', ''),
                    mimetype=attachment.get('mimetype', None)
                )
        
        return email

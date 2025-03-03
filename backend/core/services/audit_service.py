"""
Сервис для работы с аудитом.

Этот модуль предоставляет сервис для работы с аудитом действий пользователей.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Type

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from core.models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLogEntry:
    """
    Класс для представления записи аудита.
    """
    
    def __init__(self, action: str, model_name: str, object_id: str, object_repr: str,
                 changes: Dict[str, Any], user: Optional[User] = None,
                 ip_address: Optional[str] = None, timestamp: Optional[datetime] = None):
        """
        Инициализирует запись аудита.
        
        Args:
            action: Действие (create, update, delete)
            model_name: Имя модели
            object_id: ID объекта
            object_repr: Строковое представление объекта
            changes: Изменения в объекте
            user: Пользователь, выполнивший действие
            ip_address: IP-адрес пользователя
            timestamp: Время действия
        """
        self.action = action
        self.model_name = model_name
        self.object_id = object_id
        self.object_repr = object_repr
        self.changes = changes
        self.user = user
        self.ip_address = ip_address
        self.timestamp = timestamp or timezone.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует запись аудита в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными записи аудита
        """
        return {
            'action': self.action,
            'model_name': self.model_name,
            'object_id': self.object_id,
            'object_repr': self.object_repr,
            'changes': self.changes,
            'user': self.user.username if self.user else None,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLogEntry':
        """
        Создает запись аудита из словаря.
        
        Args:
            data: Словарь с данными записи аудита
            
        Returns:
            AuditLogEntry: Созданная запись аудита
        """
        user = None
        if data.get('user'):
            try:
                user = User.objects.get(username=data['user'])
            except User.DoesNotExist:
                pass
        
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            action=data['action'],
            model_name=data['model_name'],
            object_id=data['object_id'],
            object_repr=data['object_repr'],
            changes=data['changes'],
            user=user,
            ip_address=data.get('ip_address'),
            timestamp=timestamp,
        )
    
    @classmethod
    def from_model(cls, audit_log: AuditLog) -> 'AuditLogEntry':
        """
        Создает запись аудита из модели AuditLog.
        
        Args:
            audit_log: Модель AuditLog
            
        Returns:
            AuditLogEntry: Созданная запись аудита
        """
        return cls(
            action=audit_log.action,
            model_name=audit_log.model_name,
            object_id=audit_log.object_id,
            object_repr=audit_log.object_repr,
            changes=audit_log.changes,
            user=audit_log.user,
            ip_address=audit_log.ip_address,
            timestamp=audit_log.timestamp,
        )


class AuditLogFilter:
    """
    Класс для фильтрации записей аудита.
    """
    
    def __init__(self, user: Optional[User] = None, action: Optional[str] = None,
                 model_name: Optional[str] = None, object_id: Optional[str] = None,
                 start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                 ip_address: Optional[str] = None):
        """
        Инициализирует фильтр записей аудита.
        
        Args:
            user: Пользователь
            action: Действие
            model_name: Имя модели
            object_id: ID объекта
            start_date: Начальная дата
            end_date: Конечная дата
            ip_address: IP-адрес
        """
        self.user = user
        self.action = action
        self.model_name = model_name
        self.object_id = object_id
        self.start_date = start_date
        self.end_date = end_date
        self.ip_address = ip_address
    
    def get_queryset(self) -> models.QuerySet:
        """
        Возвращает отфильтрованный QuerySet.
        
        Returns:
            models.QuerySet: Отфильтрованный QuerySet
        """
        queryset = AuditLog.objects.all()
        
        if self.user:
            queryset = queryset.filter(user=self.user)
        
        if self.action:
            queryset = queryset.filter(action=self.action)
        
        if self.model_name:
            queryset = queryset.filter(model_name=self.model_name)
        
        if self.object_id:
            queryset = queryset.filter(object_id=self.object_id)
        
        if self.start_date:
            queryset = queryset.filter(timestamp__gte=self.start_date)
        
        if self.end_date:
            queryset = queryset.filter(timestamp__lte=self.end_date)
        
        if self.ip_address:
            queryset = queryset.filter(ip_address=self.ip_address)
        
        return queryset.order_by('-timestamp')


class AuditService:
    """
    Сервис для работы с аудитом.
    """
    
    def __init__(self, user: Optional[User] = None, ip_address: Optional[str] = None):
        """
        Инициализирует сервис аудита.
        
        Args:
            user: Пользователь
            ip_address: IP-адрес пользователя
        """
        self.user = user
        self.ip_address = ip_address
    
    def log_create(self, instance: models.Model) -> AuditLog:
        """
        Логирует создание объекта.
        
        Args:
            instance: Созданный объект
            
        Returns:
            AuditLog: Запись аудита
        """
        model_name = instance.__class__.__name__
        object_id = str(instance.pk)
        object_repr = str(instance)
        
        # Получаем все поля объекта
        changes = {}
        for field in instance._meta.fields:
            if field.name not in ['created_at', 'updated_at']:
                value = getattr(instance, field.name)
                if isinstance(value, models.Model):
                    value = str(value)
                changes[field.name] = value
        
        return self._create_audit_log('create', model_name, object_id, object_repr, changes)
    
    def log_update(self, instance: models.Model, changed_fields: Optional[List[str]] = None) -> AuditLog:
        """
        Логирует обновление объекта.
        
        Args:
            instance: Обновленный объект
            changed_fields: Список измененных полей
            
        Returns:
            AuditLog: Запись аудита
        """
        model_name = instance.__class__.__name__
        object_id = str(instance.pk)
        object_repr = str(instance)
        
        # Получаем измененные поля объекта
        changes = {}
        if changed_fields:
            for field_name in changed_fields:
                if hasattr(instance, field_name):
                    value = getattr(instance, field_name)
                    if isinstance(value, models.Model):
                        value = str(value)
                    changes[field_name] = value
        else:
            # Если список измененных полей не указан, логируем все поля
            for field in instance._meta.fields:
                if field.name not in ['created_at', 'updated_at']:
                    value = getattr(instance, field.name)
                    if isinstance(value, models.Model):
                        value = str(value)
                    changes[field.name] = value
        
        return self._create_audit_log('update', model_name, object_id, object_repr, changes)
    
    def log_delete(self, instance: models.Model) -> AuditLog:
        """
        Логирует удаление объекта.
        
        Args:
            instance: Удаленный объект
            
        Returns:
            AuditLog: Запись аудита
        """
        model_name = instance.__class__.__name__
        object_id = str(instance.pk)
        object_repr = str(instance)
        
        # Для удаления не нужно логировать изменения
        changes = {}
        
        return self._create_audit_log('delete', model_name, object_id, object_repr, changes)
    
    def _create_audit_log(self, action: str, model_name: str, object_id: str,
                         object_repr: str, changes: Dict[str, Any]) -> AuditLog:
        """
        Создает запись аудита.
        
        Args:
            action: Действие
            model_name: Имя модели
            object_id: ID объекта
            object_repr: Строковое представление объекта
            changes: Изменения в объекте
            
        Returns:
            AuditLog: Запись аудита
        """
        audit_log = AuditLog.objects.create(
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            user=self.user,
            ip_address=self.ip_address,
        )
        
        logger.info(
            f"{action.capitalize()} {model_name}: {object_repr} "
            f"(by {self.user.username if self.user else 'anonymous'} "
            f"from {self.ip_address or 'unknown'})"
        )
        
        return audit_log
    
    def get_audit_logs(self, filter_params: Optional[AuditLogFilter] = None) -> List[AuditLogEntry]:
        """
        Получает записи аудита.
        
        Args:
            filter_params: Параметры фильтрации
            
        Returns:
            List[AuditLogEntry]: Список записей аудита
        """
        queryset = AuditLog.objects.all().order_by('-timestamp')
        
        if filter_params:
            queryset = filter_params.get_queryset()
        
        return [AuditLogEntry.from_model(audit_log) for audit_log in queryset]
    
    def get_audit_log(self, audit_log_id: int) -> Optional[AuditLogEntry]:
        """
        Получает запись аудита по ID.
        
        Args:
            audit_log_id: ID записи аудита
            
        Returns:
            Optional[AuditLogEntry]: Запись аудита или None, если запись не найдена
        """
        try:
            audit_log = AuditLog.objects.get(pk=audit_log_id)
            return AuditLogEntry.from_model(audit_log)
        except AuditLog.DoesNotExist:
            return None
    
    def search_audit_logs(self, query: str) -> List[AuditLogEntry]:
        """
        Ищет записи аудита по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            List[AuditLogEntry]: Список записей аудита
        """
        queryset = AuditLog.objects.filter(
            Q(model_name__icontains=query) |
            Q(object_repr__icontains=query) |
            Q(action__icontains=query) |
            Q(object_id__icontains=query)
        ).order_by('-timestamp')
        
        return [AuditLogEntry.from_model(audit_log) for audit_log in queryset]
    
    def export_audit_logs(self, filter_params: Optional[AuditLogFilter] = None) -> str:
        """
        Экспортирует записи аудита в формате JSON.
        
        Args:
            filter_params: Параметры фильтрации
            
        Returns:
            str: Записи аудита в формате JSON
        """
        audit_logs = self.get_audit_logs(filter_params)
        audit_logs_dict = [audit_log.to_dict() for audit_log in audit_logs]
        
        return json.dumps(audit_logs_dict, indent=2)
    
    def import_audit_logs(self, json_data: str) -> List[AuditLog]:
        """
        Импортирует записи аудита из формата JSON.
        
        Args:
            json_data: Записи аудита в формате JSON
            
        Returns:
            List[AuditLog]: Список импортированных записей аудита
        """
        audit_logs_dict = json.loads(json_data)
        imported_logs = []
        
        for audit_log_dict in audit_logs_dict:
            audit_log_entry = AuditLogEntry.from_dict(audit_log_dict)
            
            audit_log = AuditLog.objects.create(
                action=audit_log_entry.action,
                model_name=audit_log_entry.model_name,
                object_id=audit_log_entry.object_id,
                object_repr=audit_log_entry.object_repr,
                changes=audit_log_entry.changes,
                user=audit_log_entry.user,
                ip_address=audit_log_entry.ip_address,
                timestamp=audit_log_entry.timestamp,
            )
            
            imported_logs.append(audit_log)
        
        return imported_logs

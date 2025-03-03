"""
Команда для очистки старых данных.

Эта команда удаляет устаревшие данные из базы данных,
такие как старые логи, уведомления и временные файлы.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from core.models import AuditLog, LoginAttempt, Notification


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Команда Django для очистки старых данных.
    """
    
    help = 'Очищает старые данные из базы данных'
    
    def add_arguments(self, parser):
        """
        Добавляет аргументы командной строки.
        
        Args:
            parser: Парсер аргументов
        """
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Удалить данные старше указанного количества дней (по умолчанию 90)'
        )
        
        parser.add_argument(
            '--audit-logs',
            action='store_true',
            help='Очистить старые записи аудита'
        )
        
        parser.add_argument(
            '--login-attempts',
            action='store_true',
            help='Очистить старые попытки входа'
        )
        
        parser.add_argument(
            '--notifications',
            action='store_true',
            help='Очистить старые уведомления'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать, что будет удалено, без фактического удаления'
        )
    
    def handle(self, *args, **options):
        """
        Выполняет команду.
        
        Args:
            *args: Позиционные аргументы
            **options: Именованные аргументы
        """
        days = options['days']
        audit_logs = options['audit_logs']
        login_attempts = options['login_attempts']
        notifications = options['notifications']
        dry_run = options['dry_run']
        
        # Если не указаны конкретные типы данных, очищаем все
        if not any([audit_logs, login_attempts, notifications]):
            audit_logs = login_attempts = notifications = True
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Очистка данных старше {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Режим тестового запуска - данные не будут удалены"))
        
        # Очистка записей аудита
        if audit_logs:
            count = self._cleanup_audit_logs(cutoff_date, dry_run)
            self.stdout.write(f"Записи аудита: {count} записей")
        
        # Очистка попыток входа
        if login_attempts:
            count = self._cleanup_login_attempts(cutoff_date, dry_run)
            self.stdout.write(f"Попытки входа: {count} записей")
        
        # Очистка уведомлений
        if notifications:
            count = self._cleanup_notifications(cutoff_date, dry_run)
            self.stdout.write(f"Уведомления: {count} записей")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Это был тестовый запуск. Используйте команду без --dry-run для фактического удаления."))
        else:
            self.stdout.write(self.style.SUCCESS("Очистка завершена успешно"))
    
    def _cleanup_audit_logs(self, cutoff_date: datetime, dry_run: bool) -> int:
        """
        Очищает старые записи аудита.
        
        Args:
            cutoff_date: Дата отсечения
            dry_run: Режим тестового запуска
            
        Returns:
            int: Количество удаленных записей
        """
        queryset = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        count = queryset.count()
        
        if not dry_run:
            queryset.delete()
            logger.info(f"Удалено {count} записей аудита старше {cutoff_date}")
        
        return count
    
    def _cleanup_login_attempts(self, cutoff_date: datetime, dry_run: bool) -> int:
        """
        Очищает старые попытки входа.
        
        Args:
            cutoff_date: Дата отсечения
            dry_run: Режим тестового запуска
            
        Returns:
            int: Количество удаленных записей
        """
        queryset = LoginAttempt.objects.filter(timestamp__lt=cutoff_date)
        count = queryset.count()
        
        if not dry_run:
            queryset.delete()
            logger.info(f"Удалено {count} попыток входа старше {cutoff_date}")
        
        return count
    
    def _cleanup_notifications(self, cutoff_date: datetime, dry_run: bool) -> int:
        """
        Очищает старые уведомления.
        
        Args:
            cutoff_date: Дата отсечения
            dry_run: Режим тестового запуска
            
        Returns:
            int: Количество удаленных записей
        """
        queryset = Notification.objects.filter(
            Q(created_at__lt=cutoff_date) & 
            (Q(is_read=True) | Q(is_sent=True))
        )
        count = queryset.count()
        
        if not dry_run:
            queryset.delete()
            logger.info(f"Удалено {count} уведомлений старше {cutoff_date}")
        
        return count

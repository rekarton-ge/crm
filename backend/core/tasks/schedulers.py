"""
Планировщики задач для CRM системы.

Этот модуль предоставляет классы и функции для планирования и управления
периодическими задачами в системе.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, Type

from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from django.utils import timezone

from core.tasks.base_task import BaseTask

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Базовый класс для планировщиков задач.
    """
    
    def __init__(self, app: Celery):
        """
        Инициализирует планировщик задач.
        
        Args:
            app: Экземпляр приложения Celery
        """
        self.app = app
        self.scheduled_tasks = {}
    
    def register_task(self, task: Union[str, Type[BaseTask]], schedule: Any, 
                     args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                     name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует задачу в планировщике.
        
        Args:
            task: Задача или имя задачи
            schedule: Расписание выполнения задачи
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        task_name = name or (task.__name__ if isinstance(task, type) else task)
        
        if task_name in self.scheduled_tasks:
            logger.warning(f"Task {task_name} already registered, overwriting")
        
        self.scheduled_tasks[task_name] = {
            'task': task.__name__ if isinstance(task, type) else task,
            'schedule': schedule,
            'args': args or [],
            'kwargs': kwargs or {},
            'enabled': enabled,
        }
        
        logger.info(f"Task {task_name} registered with schedule {schedule}")
        
        return task_name
    
    def unregister_task(self, name: str) -> bool:
        """
        Отменяет регистрацию задачи.
        
        Args:
            name: Имя задачи
            
        Returns:
            bool: True, если задача была отменена, иначе False
        """
        if name in self.scheduled_tasks:
            del self.scheduled_tasks[name]
            logger.info(f"Task {name} unregistered")
            return True
        
        logger.warning(f"Task {name} not found")
        return False
    
    def enable_task(self, name: str) -> bool:
        """
        Включает задачу.
        
        Args:
            name: Имя задачи
            
        Returns:
            bool: True, если задача была включена, иначе False
        """
        if name in self.scheduled_tasks:
            self.scheduled_tasks[name]['enabled'] = True
            logger.info(f"Task {name} enabled")
            return True
        
        logger.warning(f"Task {name} not found")
        return False
    
    def disable_task(self, name: str) -> bool:
        """
        Отключает задачу.
        
        Args:
            name: Имя задачи
            
        Returns:
            bool: True, если задача была отключена, иначе False
        """
        if name in self.scheduled_tasks:
            self.scheduled_tasks[name]['enabled'] = False
            logger.info(f"Task {name} disabled")
            return True
        
        logger.warning(f"Task {name} not found")
        return False
    
    def get_task(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о задаче.
        
        Args:
            name: Имя задачи
            
        Returns:
            Optional[Dict[str, Any]]: Информация о задаче или None, если задача не найдена
        """
        return self.scheduled_tasks.get(name)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает информацию о всех задачах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Информация о всех задачах
        """
        return self.scheduled_tasks
    
    def get_enabled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает информацию о включенных задачах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Информация о включенных задачах
        """
        return {name: task for name, task in self.scheduled_tasks.items() if task['enabled']}
    
    def get_disabled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает информацию о отключенных задачах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Информация о отключенных задачах
        """
        return {name: task for name, task in self.scheduled_tasks.items() if not task['enabled']}
    
    def apply_schedules(self) -> None:
        """
        Применяет расписания задач к приложению Celery.
        """
        beat_schedule = {}
        
        for name, task in self.scheduled_tasks.items():
            if task['enabled']:
                beat_schedule[name] = {
                    'task': task['task'],
                    'schedule': task['schedule'],
                    'args': task['args'],
                    'kwargs': task['kwargs'],
                }
        
        self.app.conf.beat_schedule = beat_schedule
        logger.info(f"Applied {len(beat_schedule)} schedules to Celery")


class CronScheduler(TaskScheduler):
    """
    Планировщик задач на основе cron-выражений.
    """
    
    def register_cron_task(self, task: Union[str, Type[BaseTask]], 
                          minute: str = '*', hour: str = '*', day_of_week: str = '*',
                          day_of_month: str = '*', month_of_year: str = '*',
                          args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                          name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует задачу с расписанием в формате cron.
        
        Args:
            task: Задача или имя задачи
            minute: Минуты (0-59)
            hour: Часы (0-23)
            day_of_week: День недели (0-6 или mon, tue, wed, thu, fri, sat, sun)
            day_of_month: День месяца (1-31)
            month_of_year: Месяц (1-12 или jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec)
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        schedule = crontab(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year
        )
        
        return self.register_task(task, schedule, args, kwargs, name, enabled)
    
    def register_daily_task(self, task: Union[str, Type[BaseTask]], hour: int, minute: int = 0,
                           args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                           name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует ежедневную задачу.
        
        Args:
            task: Задача или имя задачи
            hour: Час выполнения (0-23)
            minute: Минута выполнения (0-59)
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        return self.register_cron_task(
            task=task,
            minute=str(minute),
            hour=str(hour),
            args=args,
            kwargs=kwargs,
            name=name,
            enabled=enabled
        )
    
    def register_weekly_task(self, task: Union[str, Type[BaseTask]], day_of_week: Union[int, str],
                            hour: int = 0, minute: int = 0,
                            args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                            name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует еженедельную задачу.
        
        Args:
            task: Задача или имя задачи
            day_of_week: День недели (0-6 или mon, tue, wed, thu, fri, sat, sun)
            hour: Час выполнения (0-23)
            minute: Минута выполнения (0-59)
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        return self.register_cron_task(
            task=task,
            minute=str(minute),
            hour=str(hour),
            day_of_week=str(day_of_week),
            args=args,
            kwargs=kwargs,
            name=name,
            enabled=enabled
        )
    
    def register_monthly_task(self, task: Union[str, Type[BaseTask]], day_of_month: int,
                             hour: int = 0, minute: int = 0,
                             args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                             name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует ежемесячную задачу.
        
        Args:
            task: Задача или имя задачи
            day_of_month: День месяца (1-31)
            hour: Час выполнения (0-23)
            minute: Минута выполнения (0-59)
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        return self.register_cron_task(
            task=task,
            minute=str(minute),
            hour=str(hour),
            day_of_month=str(day_of_month),
            args=args,
            kwargs=kwargs,
            name=name,
            enabled=enabled
        )


class IntervalScheduler(TaskScheduler):
    """
    Планировщик задач на основе интервалов.
    """
    
    def register_interval_task(self, task: Union[str, Type[BaseTask]], 
                              seconds: Optional[int] = None, minutes: Optional[int] = None,
                              hours: Optional[int] = None, days: Optional[int] = None,
                              args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                              name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует задачу с интервальным расписанием.
        
        Args:
            task: Задача или имя задачи
            seconds: Интервал в секундах
            minutes: Интервал в минутах
            hours: Интервал в часах
            days: Интервал в днях
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        interval = timedelta(
            seconds=seconds or 0,
            minutes=minutes or 0,
            hours=hours or 0,
            days=days or 0
        )
        
        if interval.total_seconds() == 0:
            raise ValueError("Interval must be greater than 0")
        
        return self.register_task(task, interval, args, kwargs, name, enabled)
    
    def register_hourly_task(self, task: Union[str, Type[BaseTask]], minute: int = 0,
                            args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                            name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует ежечасную задачу.
        
        Args:
            task: Задача или имя задачи
            minute: Минута выполнения (0-59)
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        # Для ежечасной задачи используем cron-выражение
        cron_scheduler = CronScheduler(self.app)
        return cron_scheduler.register_cron_task(
            task=task,
            minute=str(minute),
            args=args,
            kwargs=kwargs,
            name=name,
            enabled=enabled
        )
    
    def register_minutely_task(self, task: Union[str, Type[BaseTask]], 
                              args: Optional[List] = None, kwargs: Optional[Dict] = None, 
                              name: Optional[str] = None, enabled: bool = True) -> str:
        """
        Регистрирует ежеминутную задачу.
        
        Args:
            task: Задача или имя задачи
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            name: Имя задачи
            enabled: Включена ли задача
            
        Returns:
            str: Имя зарегистрированной задачи
        """
        return self.register_interval_task(
            task=task,
            minutes=1,
            args=args,
            kwargs=kwargs,
            name=name,
            enabled=enabled
        )


# Создаем экземпляры планировщиков
from core.tasks.celery_app import app

cron_scheduler = CronScheduler(app)
interval_scheduler = IntervalScheduler(app)


# Функции-обертки для совместимости с импортами в __init__.py
def get_schedule() -> Dict[str, Dict[str, Any]]:
    """
    Получает текущее расписание задач.
    
    Returns:
        Dict[str, Dict[str, Any]]: Текущее расписание задач
    """
    return app.conf.beat_schedule


def register_periodic_task(task: Union[str, Type[BaseTask]], 
                          schedule: Any,
                          args: Optional[List] = None, 
                          kwargs: Optional[Dict] = None, 
                          name: Optional[str] = None, 
                          enabled: bool = True) -> str:
    """
    Регистрирует периодическую задачу.
    
    Args:
        task: Задача или имя задачи
        schedule: Расписание выполнения задачи
        args: Аргументы задачи
        kwargs: Именованные аргументы задачи
        name: Имя задачи
        enabled: Включена ли задача
        
    Returns:
        str: Имя зарегистрированной задачи
    """
    if isinstance(schedule, crontab):
        return cron_scheduler.register_task(task, schedule, args, kwargs, name, enabled)
    else:
        return interval_scheduler.register_task(task, schedule, args, kwargs, name, enabled)


def unregister_periodic_task(name: str) -> bool:
    """
    Отменяет регистрацию периодической задачи.
    
    Args:
        name: Имя задачи
        
    Returns:
        bool: True, если задача была отменена, иначе False
    """
    # Пробуем отменить в обоих планировщиках
    cron_result = cron_scheduler.unregister_task(name)
    interval_result = interval_scheduler.unregister_task(name)
    
    return cron_result or interval_result


# Экспортируем планировщики и функции
__all__ = [
    'TaskScheduler',
    'CronScheduler',
    'IntervalScheduler',
    'cron_scheduler',
    'interval_scheduler',
    'get_schedule',
    'register_periodic_task',
    'unregister_periodic_task',
]

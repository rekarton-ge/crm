"""
Задачи Celery.

Этот пакет содержит задачи Celery для асинхронного выполнения.
"""

from core.tasks.celery_app import app
from core.tasks.base_task import BaseTask
from core.tasks.decorators import (
    retry_task, task_with_logging, task_with_metrics, task_with_notification
)
from core.tasks.monitors import (
    TaskMonitor, TaskStatusMonitor, TaskPerformanceMonitor
)
from core.tasks.schedulers import (
    TaskScheduler, CronScheduler, IntervalScheduler,
    cron_scheduler, interval_scheduler,
    get_schedule, register_periodic_task, unregister_periodic_task
)


__all__ = [
    'app',
    'BaseTask',
    'retry_task',
    'task_with_logging',
    'task_with_metrics',
    'task_with_notification',
    'TaskMonitor',
    'TaskStatusMonitor',
    'TaskPerformanceMonitor',
    'TaskScheduler',
    'CronScheduler',
    'IntervalScheduler',
    'cron_scheduler',
    'interval_scheduler',
    'get_schedule',
    'register_periodic_task',
    'unregister_periodic_task',
]

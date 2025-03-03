"""
Настройки Celery.

Этот модуль содержит настройки Celery для асинхронного выполнения задач.
"""

import os
from typing import Any, Dict, List, Optional, Union

from celery import Celery
from django.conf import settings


# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр Celery
app = Celery('crm')

# Загружаем настройки из Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в приложениях Django
app.autodiscover_tasks()


# Настройки Celery по умолчанию
app.conf.update(
    # Брокер сообщений
    broker_url=getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    
    # Бэкенд результатов
    result_backend=getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Формат сериализации
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Часовой пояс
    timezone=getattr(settings, 'TIME_ZONE', 'UTC'),
    
    # Включаем UTC
    enable_utc=True,
    
    # Настройки воркеров
    worker_concurrency=getattr(settings, 'CELERY_WORKER_CONCURRENCY', 4),
    worker_prefetch_multiplier=getattr(settings, 'CELERY_WORKER_PREFETCH_MULTIPLIER', 1),
    worker_max_tasks_per_child=getattr(settings, 'CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000),
    
    # Настройки задач
    task_time_limit=getattr(settings, 'CELERY_TASK_TIME_LIMIT', 3600),
    task_soft_time_limit=getattr(settings, 'CELERY_TASK_SOFT_TIME_LIMIT', 3600),
    
    # Настройки повторных попыток
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Настройки очередей
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'high_priority': {
            'exchange': 'high_priority',
            'routing_key': 'high_priority',
        },
        'low_priority': {
            'exchange': 'low_priority',
            'routing_key': 'low_priority',
        },
    },
    
    # Настройки маршрутизации
    task_routes={
        'core.tasks.*': {'queue': 'default'},
        'core.tasks.high_priority.*': {'queue': 'high_priority'},
        'core.tasks.low_priority.*': {'queue': 'low_priority'},
    },
    
    # Настройки периодических задач
    beat_schedule=getattr(settings, 'CELERY_BEAT_SCHEDULE', {}),
)


@app.task(bind=True)
def debug_task(self):
    """
    Отладочная задача.
    
    Выводит информацию о запросе.
    """
    print(f'Request: {self.request!r}')


if __name__ == '__main__':
    app.start()

"""
Мониторы для задач Celery.

Этот модуль содержит классы для мониторинга задач Celery,
включая проверку состояния воркеров и задач.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from celery import Celery
from celery.events import Event
from celery.events.receiver import EventReceiver
from celery.events.state import State, Task
from celery.app.control import Inspect
from django.conf import settings
from django.utils import timezone

from core.tasks.celery_app import app


logger = logging.getLogger('tasks.monitors')


class TaskMonitor:
    """
    Базовый класс для мониторинга задач Celery.
    
    Предоставляет базовую функциональность для мониторинга задач Celery.
    """
    
    def __init__(self, app: Optional[Celery] = None):
        """
        Инициализация монитора задач.
        
        Args:
            app (Celery, optional): Экземпляр Celery.
        """
        self.app = app or globals().get('app')
        self.inspector = Inspect(app=self.app)
    
    def get_active_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Возвращает активные задачи.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Словарь с активными задачами по воркерам.
        """
        return self.inspector.active() or {}
    
    def get_reserved_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Возвращает зарезервированные задачи.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Словарь с зарезервированными задачами по воркерам.
        """
        return self.inspector.reserved() or {}
    
    def get_scheduled_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Возвращает запланированные задачи.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Словарь с запланированными задачами по воркерам.
        """
        return self.inspector.scheduled() or {}
    
    def get_revoked_tasks(self) -> Dict[str, List[str]]:
        """
        Возвращает отмененные задачи.
        
        Returns:
            Dict[str, List[str]]: Словарь с отмененными задачами по воркерам.
        """
        return self.inspector.revoked() or {}
    
    def get_registered_tasks(self) -> Dict[str, List[str]]:
        """
        Возвращает зарегистрированные задачи.
        
        Returns:
            Dict[str, List[str]]: Словарь с зарегистрированными задачами по воркерам.
        """
        return self.inspector.registered() or {}
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает статистику воркеров.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь со статистикой по воркерам.
        """
        return self.inspector.stats() or {}
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о задаче.
        
        Args:
            task_id (str): Идентификатор задачи.
        
        Returns:
            Optional[Dict[str, Any]]: Информация о задаче или None, если задача не найдена.
        """
        # Проверяем активные задачи
        active_tasks = self.get_active_tasks()
        for worker, tasks in active_tasks.items():
            for task in tasks:
                if task.get('id') == task_id:
                    task['status'] = 'active'
                    task['worker'] = worker
                    return task
        
        # Проверяем зарезервированные задачи
        reserved_tasks = self.get_reserved_tasks()
        for worker, tasks in reserved_tasks.items():
            for task in tasks:
                if task.get('id') == task_id:
                    task['status'] = 'reserved'
                    task['worker'] = worker
                    return task
        
        # Проверяем запланированные задачи
        scheduled_tasks = self.get_scheduled_tasks()
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                if task.get('id') == task_id:
                    task['status'] = 'scheduled'
                    task['worker'] = worker
                    return task
        
        # Проверяем отмененные задачи
        revoked_tasks = self.get_revoked_tasks()
        for worker, tasks in revoked_tasks.items():
            if task_id in tasks:
                return {
                    'id': task_id,
                    'status': 'revoked',
                    'worker': worker
                }
        
        return None
    
    def get_worker_info(self, worker_name: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о воркере.
        
        Args:
            worker_name (str): Имя воркера.
        
        Returns:
            Optional[Dict[str, Any]]: Информация о воркере или None, если воркер не найден.
        """
        stats = self.get_stats()
        return stats.get(worker_name)
    
    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """
        Возвращает информацию об очереди.
        
        Args:
            queue_name (str): Имя очереди.
        
        Returns:
            Dict[str, Any]: Информация об очереди.
        """
        # Получаем информацию о задачах в очереди
        active_tasks = self.get_active_tasks()
        reserved_tasks = self.get_reserved_tasks()
        scheduled_tasks = self.get_scheduled_tasks()
        
        # Фильтруем задачи по очереди
        active_queue_tasks = []
        reserved_queue_tasks = []
        scheduled_queue_tasks = []
        
        for worker, tasks in active_tasks.items():
            for task in tasks:
                if task.get('delivery_info', {}).get('routing_key') == queue_name:
                    task['worker'] = worker
                    active_queue_tasks.append(task)
        
        for worker, tasks in reserved_tasks.items():
            for task in tasks:
                if task.get('delivery_info', {}).get('routing_key') == queue_name:
                    task['worker'] = worker
                    reserved_queue_tasks.append(task)
        
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                if task.get('delivery_info', {}).get('routing_key') == queue_name:
                    task['worker'] = worker
                    scheduled_queue_tasks.append(task)
        
        return {
            'name': queue_name,
            'active_tasks': active_queue_tasks,
            'reserved_tasks': reserved_queue_tasks,
            'scheduled_tasks': scheduled_queue_tasks,
            'total_tasks': len(active_queue_tasks) + len(reserved_queue_tasks) + len(scheduled_queue_tasks)
        }


class TaskStatusMonitor(TaskMonitor):
    """
    Монитор статусов задач Celery.
    
    Отслеживает изменения статусов задач Celery.
    """
    
    def __init__(self, app: Optional[Celery] = None):
        """
        Инициализация монитора статусов задач.
        
        Args:
            app (Celery, optional): Экземпляр Celery.
        """
        super().__init__(app)
        self.state = State()
        self.receiver = None
    
    def start(self) -> None:
        """
        Запускает монитор статусов задач.
        """
        if self.receiver is not None:
            return
        
        self.receiver = self.app.events.Receiver(
            connection=self.app.connection(),
            handlers={
                'task-sent': self.on_task_sent,
                'task-received': self.on_task_received,
                'task-started': self.on_task_started,
                'task-succeeded': self.on_task_succeeded,
                'task-failed': self.on_task_failed,
                'task-rejected': self.on_task_rejected,
                'task-revoked': self.on_task_revoked,
                'task-retried': self.on_task_retried
            }
        )
        
        # Запускаем получение событий в отдельном потоке
        import threading
        self.thread = threading.Thread(target=self.receiver.capture, kwargs={'limit': None, 'timeout': None})
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self) -> None:
        """
        Останавливает монитор статусов задач.
        """
        if self.receiver is not None:
            self.receiver.should_stop = True
            self.receiver = None
    
    def on_task_sent(self, event: Event) -> None:
        """
        Обработчик события отправки задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.debug(f"Задача {task.name}[{task.uuid}] отправлена")
    
    def on_task_received(self, event: Event) -> None:
        """
        Обработчик события получения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.debug(f"Задача {task.name}[{task.uuid}] получена")
    
    def on_task_started(self, event: Event) -> None:
        """
        Обработчик события начала выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.debug(f"Задача {task.name}[{task.uuid}] начала выполняться")
    
    def on_task_succeeded(self, event: Event) -> None:
        """
        Обработчик события успешного выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.debug(f"Задача {task.name}[{task.uuid}] успешно выполнена")
    
    def on_task_failed(self, event: Event) -> None:
        """
        Обработчик события ошибки выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.error(f"Задача {task.name}[{task.uuid}] завершилась с ошибкой: {event.get('exception')}")
    
    def on_task_rejected(self, event: Event) -> None:
        """
        Обработчик события отклонения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.warning(f"Задача {task.name}[{task.uuid}] отклонена")
    
    def on_task_revoked(self, event: Event) -> None:
        """
        Обработчик события отмены задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.warning(f"Задача {task.name}[{task.uuid}] отменена")
    
    def on_task_retried(self, event: Event) -> None:
        """
        Обработчик события повторной попытки выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        self.state.event(event)
        task = self.state.tasks.get(event['uuid'])
        logger.warning(f"Задача {task.name}[{task.uuid}] будет выполнена повторно")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает статус задачи.
        
        Args:
            task_id (str): Идентификатор задачи.
        
        Returns:
            Optional[Dict[str, Any]]: Статус задачи или None, если задача не найдена.
        """
        task = self.state.tasks.get(task_id)
        
        if task is None:
            return None
        
        return {
            'id': task.uuid,
            'name': task.name,
            'args': task.args,
            'kwargs': task.kwargs,
            'status': task.state,
            'worker': task.worker.hostname if task.worker else None,
            'timestamp': task.timestamp,
            'runtime': task.runtime,
            'result': task.result,
            'exception': task.exception,
            'traceback': task.traceback
        }
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Возвращает задачи с указанным статусом.
        
        Args:
            status (str): Статус задачи.
        
        Returns:
            List[Dict[str, Any]]: Список задач с указанным статусом.
        """
        tasks = []
        
        for task_id, task in self.state.tasks.items():
            if task.state == status:
                tasks.append({
                    'id': task.uuid,
                    'name': task.name,
                    'args': task.args,
                    'kwargs': task.kwargs,
                    'status': task.state,
                    'worker': task.worker.hostname if task.worker else None,
                    'timestamp': task.timestamp,
                    'runtime': task.runtime,
                    'result': task.result,
                    'exception': task.exception,
                    'traceback': task.traceback
                })
        
        return tasks
    
    def get_tasks_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Возвращает задачи с указанным именем.
        
        Args:
            name (str): Имя задачи.
        
        Returns:
            List[Dict[str, Any]]: Список задач с указанным именем.
        """
        tasks = []
        
        for task_id, task in self.state.tasks.items():
            if task.name == name:
                tasks.append({
                    'id': task.uuid,
                    'name': task.name,
                    'args': task.args,
                    'kwargs': task.kwargs,
                    'status': task.state,
                    'worker': task.worker.hostname if task.worker else None,
                    'timestamp': task.timestamp,
                    'runtime': task.runtime,
                    'result': task.result,
                    'exception': task.exception,
                    'traceback': task.traceback
                })
        
        return tasks


class TaskPerformanceMonitor(TaskMonitor):
    """
    Монитор производительности задач Celery.
    
    Отслеживает производительность задач Celery.
    """
    
    def __init__(self, app: Optional[Celery] = None):
        """
        Инициализация монитора производительности задач.
        
        Args:
            app (Celery, optional): Экземпляр Celery.
        """
        super().__init__(app)
        self.task_stats = {}
    
    def start(self) -> None:
        """
        Запускает монитор производительности задач.
        """
        # Регистрируем обработчики событий
        self.app.events.register_dispatcher(self)
        
        # Регистрируем обработчики для событий задач
        self.app.events.add_handler('task-sent', self.on_task_sent)
        self.app.events.add_handler('task-received', self.on_task_received)
        self.app.events.add_handler('task-started', self.on_task_started)
        self.app.events.add_handler('task-succeeded', self.on_task_succeeded)
        self.app.events.add_handler('task-failed', self.on_task_failed)
        self.app.events.add_handler('task-rejected', self.on_task_rejected)
        self.app.events.add_handler('task-revoked', self.on_task_revoked)
        self.app.events.add_handler('task-retried', self.on_task_retried)
    
    def stop(self) -> None:
        """
        Останавливает монитор производительности задач.
        """
        # Удаляем обработчики событий
        self.app.events.remove_handler('task-sent', self.on_task_sent)
        self.app.events.remove_handler('task-received', self.on_task_received)
        self.app.events.remove_handler('task-started', self.on_task_started)
        self.app.events.remove_handler('task-succeeded', self.on_task_succeeded)
        self.app.events.remove_handler('task-failed', self.on_task_failed)
        self.app.events.remove_handler('task-rejected', self.on_task_rejected)
        self.app.events.remove_handler('task-revoked', self.on_task_revoked)
        self.app.events.remove_handler('task-retried', self.on_task_retried)
    
    def on_task_sent(self, event: Event) -> None:
        """
        Обработчик события отправки задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        task_name = event['name']
        
        if task_id not in self.task_stats:
            self.task_stats[task_id] = {
                'name': task_name,
                'sent_at': event['timestamp'],
                'received_at': None,
                'started_at': None,
                'completed_at': None,
                'status': 'sent',
                'runtime': None,
                'queue_time': None,
                'total_time': None
            }
    
    def on_task_received(self, event: Event) -> None:
        """
        Обработчик события получения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['received_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'received'
            
            # Вычисляем время в очереди
            if self.task_stats[task_id]['sent_at'] is not None:
                self.task_stats[task_id]['queue_time'] = (
                    self.task_stats[task_id]['received_at'] - self.task_stats[task_id]['sent_at']
                )
    
    def on_task_started(self, event: Event) -> None:
        """
        Обработчик события начала выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['started_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'started'
    
    def on_task_succeeded(self, event: Event) -> None:
        """
        Обработчик события успешного выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['completed_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'succeeded'
            self.task_stats[task_id]['runtime'] = event.get('runtime')
            
            # Вычисляем общее время выполнения
            if self.task_stats[task_id]['sent_at'] is not None:
                self.task_stats[task_id]['total_time'] = (
                    self.task_stats[task_id]['completed_at'] - self.task_stats[task_id]['sent_at']
                )
    
    def on_task_failed(self, event: Event) -> None:
        """
        Обработчик события ошибки выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['completed_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'failed'
            self.task_stats[task_id]['runtime'] = event.get('runtime')
            self.task_stats[task_id]['exception'] = event.get('exception')
            self.task_stats[task_id]['traceback'] = event.get('traceback')
            
            # Вычисляем общее время выполнения
            if self.task_stats[task_id]['sent_at'] is not None:
                self.task_stats[task_id]['total_time'] = (
                    self.task_stats[task_id]['completed_at'] - self.task_stats[task_id]['sent_at']
                )
    
    def on_task_rejected(self, event: Event) -> None:
        """
        Обработчик события отклонения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['completed_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'rejected'
    
    def on_task_revoked(self, event: Event) -> None:
        """
        Обработчик события отмены задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['completed_at'] = event['timestamp']
            self.task_stats[task_id]['status'] = 'revoked'
    
    def on_task_retried(self, event: Event) -> None:
        """
        Обработчик события повторной попытки выполнения задачи.
        
        Args:
            event (Event): Событие.
        """
        task_id = event['uuid']
        
        if task_id in self.task_stats:
            self.task_stats[task_id]['status'] = 'retried'
            self.task_stats[task_id]['exception'] = event.get('exception')
            self.task_stats[task_id]['traceback'] = event.get('traceback')
    
    def get_task_performance(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о производительности задачи.
        
        Args:
            task_id (str): Идентификатор задачи.
        
        Returns:
            Optional[Dict[str, Any]]: Информация о производительности задачи или None, если задача не найдена.
        """
        return self.task_stats.get(task_id)
    
    def get_task_performance_by_name(self, task_name: str) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о производительности задач с указанным именем.
        
        Args:
            task_name (str): Имя задачи.
        
        Returns:
            List[Dict[str, Any]]: Список информации о производительности задач с указанным именем.
        """
        return [
            stats for stats in self.task_stats.values()
            if stats['name'] == task_name
        ]
    
    def get_average_performance_by_name(self, task_name: str) -> Dict[str, Any]:
        """
        Возвращает среднюю производительность задач с указанным именем.
        
        Args:
            task_name (str): Имя задачи.
        
        Returns:
            Dict[str, Any]: Средняя производительность задач с указанным именем.
        """
        tasks = self.get_task_performance_by_name(task_name)
        
        if not tasks:
            return {
                'name': task_name,
                'count': 0,
                'avg_runtime': None,
                'avg_queue_time': None,
                'avg_total_time': None,
                'success_rate': None
            }
        
        # Вычисляем средние значения
        count = len(tasks)
        succeeded = sum(1 for task in tasks if task['status'] == 'succeeded')
        
        runtimes = [task['runtime'] for task in tasks if task['runtime'] is not None]
        queue_times = [task['queue_time'] for task in tasks if task['queue_time'] is not None]
        total_times = [task['total_time'] for task in tasks if task['total_time'] is not None]
        
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else None
        avg_queue_time = sum(queue_times) / len(queue_times) if queue_times else None
        avg_total_time = sum(total_times) / len(total_times) if total_times else None
        success_rate = succeeded / count if count > 0 else None
        
        return {
            'name': task_name,
            'count': count,
            'avg_runtime': avg_runtime,
            'avg_queue_time': avg_queue_time,
            'avg_total_time': avg_total_time,
            'success_rate': success_rate
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку производительности задач.
        
        Returns:
            Dict[str, Any]: Сводка производительности задач.
        """
        # Получаем уникальные имена задач
        task_names = set(task['name'] for task in self.task_stats.values())
        
        # Вычисляем среднюю производительность для каждой задачи
        task_performance = {
            task_name: self.get_average_performance_by_name(task_name)
            for task_name in task_names
        }
        
        # Вычисляем общую статистику
        total_tasks = len(self.task_stats)
        succeeded_tasks = sum(1 for task in self.task_stats.values() if task['status'] == 'succeeded')
        failed_tasks = sum(1 for task in self.task_stats.values() if task['status'] == 'failed')
        
        return {
            'total_tasks': total_tasks,
            'succeeded_tasks': succeeded_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': succeeded_tasks / total_tasks if total_tasks > 0 else None,
            'task_performance': task_performance
        }

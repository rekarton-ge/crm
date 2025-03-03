"""
Декораторы для задач Celery.

Этот модуль содержит декораторы для задач Celery.
"""

import functools
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from celery import Task, shared_task
from django.conf import settings
from django.utils import timezone

from core.tasks.celery_app import app


logger = logging.getLogger('tasks')


def retry_task(
    max_retries: int = 3,
    countdown: int = 60,
    backoff: bool = True,
    backoff_max: int = 600,
    jitter: bool = True,
    exceptions: Tuple[Exception, ...] = (Exception,)
) -> Callable:
    """
    Декоратор для повторного выполнения задачи при ошибке.
    
    Args:
        max_retries (int, optional): Максимальное количество повторных попыток.
        countdown (int, optional): Задержка перед повторной попыткой в секундах.
        backoff (bool, optional): Использовать экспоненциальную задержку.
        backoff_max (int, optional): Максимальная задержка в секундах.
        jitter (bool, optional): Добавлять случайное отклонение к задержке.
        exceptions (Tuple[Exception, ...], optional): Исключения, при которых нужно повторять задачу.
    
    Returns:
        Callable: Декоратор для задачи.
    """
    def decorator(task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = kwargs.pop('_retries', 0)
            
            try:
                return task_func(*args, **kwargs)
            except exceptions as e:
                if retries >= max_retries:
                    logger.warning(
                        f"Превышено максимальное количество попыток выполнения задачи {task_func.__name__}: "
                        f"{retries}/{max_retries}"
                    )
                    raise
                
                # Вычисляем задержку перед повторной попыткой
                delay = countdown
                
                if backoff:
                    # Экспоненциальная задержка
                    delay = delay * (2 ** retries)
                    
                    # Ограничиваем максимальную задержку
                    if backoff_max:
                        delay = min(delay, backoff_max)
                    
                    # Добавляем случайное отклонение
                    if jitter:
                        import random
                        delay = delay + random.uniform(0, delay * 0.1)
                
                logger.warning(
                    f"Повторная попытка выполнения задачи {task_func.__name__} "
                    f"({retries + 1}/{max_retries}) через {delay:.2f} сек.: {e}"
                )
                
                # Повторяем задачу
                kwargs['_retries'] = retries + 1
                app.send_task(
                    task_func.name,
                    args=args,
                    kwargs=kwargs,
                    countdown=delay
                )
        
        return wrapper
    
    return decorator


def task_with_logging(log_level: int = logging.INFO) -> Callable:
    """
    Декоратор для логирования выполнения задачи.
    
    Args:
        log_level (int, optional): Уровень логирования.
    
    Returns:
        Callable: Декоратор для задачи.
    """
    def decorator(task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Сохраняем время начала выполнения
            start_time = time.time()
            
            # Логируем начало выполнения
            logger.log(
                log_level,
                f"Начало выполнения задачи {task_func.__name__} "
                f"с аргументами: args={args}, kwargs={kwargs}"
            )
            
            try:
                # Выполняем задачу
                result = task_func(*args, **kwargs)
                
                # Сохраняем время окончания выполнения
                end_time = time.time()
                duration = end_time - start_time
                
                # Логируем успешное выполнение
                logger.log(
                    log_level,
                    f"Задача {task_func.__name__} успешно выполнена за {duration:.2f} сек."
                )
                
                return result
            except Exception as e:
                # Сохраняем время окончания выполнения
                end_time = time.time()
                duration = end_time - start_time
                
                # Логируем ошибку
                logger.error(
                    f"Ошибка выполнения задачи {task_func.__name__} за {duration:.2f} сек.: {e}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                
                # Пробрасываем исключение
                raise
        
        return wrapper
    
    return decorator


def task_with_metrics() -> Callable:
    """
    Декоратор для отправки метрик выполнения задачи.
    
    Returns:
        Callable: Декоратор для задачи.
    """
    def decorator(task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Сохраняем время начала выполнения
            start_time = time.time()
            
            try:
                # Выполняем задачу
                result = task_func(*args, **kwargs)
                
                # Сохраняем время окончания выполнения
                end_time = time.time()
                duration = end_time - start_time
                
                # Отправляем метрики успешного выполнения
                _send_metrics(
                    task_func.__name__,
                    duration,
                    success=True,
                    error=None
                )
                
                return result
            except Exception as e:
                # Сохраняем время окончания выполнения
                end_time = time.time()
                duration = end_time - start_time
                
                # Отправляем метрики ошибки выполнения
                _send_metrics(
                    task_func.__name__,
                    duration,
                    success=False,
                    error=str(e)
                )
                
                # Пробрасываем исключение
                raise
        
        return wrapper
    
    return decorator


def task_with_notification(
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
) -> Callable:
    """
    Декоратор для отправки уведомлений о выполнении задачи.
    
    Args:
        success_message (str, optional): Сообщение об успешном выполнении задачи.
        error_message (str, optional): Сообщение об ошибке выполнения задачи.
    
    Returns:
        Callable: Декоратор для задачи.
    """
    def decorator(task_func: Callable) -> Callable:
        @functools.wraps(task_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Выполняем задачу
                result = task_func(*args, **kwargs)
                
                # Отправляем уведомление об успешном выполнении
                if success_message:
                    _send_notification(
                        task_func.__name__,
                        success_message.format(
                            task_name=task_func.__name__,
                            args=args,
                            kwargs=kwargs,
                            result=result
                        ),
                        success=True
                    )
                
                return result
            except Exception as e:
                # Отправляем уведомление об ошибке выполнения
                if error_message:
                    _send_notification(
                        task_func.__name__,
                        error_message.format(
                            task_name=task_func.__name__,
                            args=args,
                            kwargs=kwargs,
                            error=str(e)
                        ),
                        success=False
                    )
                
                # Пробрасываем исключение
                raise
        
        return wrapper
    
    return decorator


def _send_metrics(
    task_name: str,
    duration: float,
    success: bool,
    error: Optional[str] = None
) -> None:
    """
    Отправляет метрики выполнения задачи.
    
    Args:
        task_name (str): Имя задачи.
        duration (float): Время выполнения задачи в секундах.
        success (bool): Флаг успешного выполнения задачи.
        error (str, optional): Сообщение об ошибке.
    """
    # Здесь можно добавить отправку метрик в систему мониторинга
    pass


def _send_notification(
    task_name: str,
    message: str,
    success: bool
) -> None:
    """
    Отправляет уведомление о выполнении задачи.
    
    Args:
        task_name (str): Имя задачи.
        message (str): Сообщение уведомления.
        success (bool): Флаг успешного выполнения задачи.
    """
    # Здесь можно добавить отправку уведомления
    pass

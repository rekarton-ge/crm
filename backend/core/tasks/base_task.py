"""
Базовый класс для задач Celery.

Этот модуль содержит базовый класс для задач Celery.
"""

import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from celery import Task
from django.conf import settings
from django.utils import timezone

from core.tasks.celery_app import app


logger = logging.getLogger('tasks')


class BaseTask(Task):
    """
    Базовый класс для задач Celery.
    
    Добавляет логирование, метрики и обработку ошибок.
    """
    
    # Абстрактная задача
    abstract = True
    
    # Настройки повторных попыток
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    # Настройки времени выполнения
    time_limit = 3600
    soft_time_limit = 3600
    
    # Настройки очереди
    queue = 'default'
    
    # Настройки логирования
    log_level = logging.INFO
    
    def __init__(self):
        """
        Инициализация задачи.
        """
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.result = None
        self.error = None
        self.retries = 0
        self.max_retries = self.retry_kwargs.get('max_retries', 3)
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Вызов задачи.
        
        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        
        Returns:
            Any: Результат выполнения задачи.
        """
        # Сохраняем время начала выполнения
        self.start_time = time.time()
        
        # Логируем начало выполнения
        self._log_start(*args, **kwargs)
        
        try:
            # Выполняем задачу
            self.result = super().__call__(*args, **kwargs)
            
            # Сохраняем время окончания выполнения
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            
            # Логируем успешное выполнение
            self._log_success(*args, **kwargs)
            
            # Отправляем метрики
            self._send_metrics(*args, **kwargs)
            
            return self.result
        except Exception as e:
            # Сохраняем время окончания выполнения
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            
            # Сохраняем ошибку
            self.error = e
            
            # Логируем ошибку
            self._log_error(e, *args, **kwargs)
            
            # Отправляем метрики
            self._send_metrics(*args, **kwargs)
            
            # Повторяем задачу
            self._retry(e, *args, **kwargs)
            
            # Пробрасываем исключение
            raise
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Обработчик повторной попытки выполнения задачи.
        
        Args:
            exc: Исключение.
            task_id: Идентификатор задачи.
            args: Позиционные аргументы.
            kwargs: Именованные аргументы.
            einfo: Информация об ошибке.
        """
        # Увеличиваем счетчик повторных попыток
        self.retries += 1
        
        # Логируем повторную попытку
        logger.warning(
            f"Повторная попытка выполнения задачи {self.name} "
            f"({self.retries}/{self.max_retries}): {exc}"
        )
        
        # Вызываем обработчик родительского класса
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Обработчик ошибки выполнения задачи.
        
        Args:
            exc: Исключение.
            task_id: Идентификатор задачи.
            args: Позиционные аргументы.
            kwargs: Именованные аргументы.
            einfo: Информация об ошибке.
        """
        # Логируем ошибку
        logger.error(
            f"Ошибка выполнения задачи {self.name}: {exc}\n"
            f"Traceback: {einfo.traceback}"
        )
        
        # Вызываем обработчик родительского класса
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """
        Обработчик успешного выполнения задачи.
        
        Args:
            retval: Результат выполнения задачи.
            task_id: Идентификатор задачи.
            args: Позиционные аргументы.
            kwargs: Именованные аргументы.
        """
        # Логируем успешное выполнение
        logger.info(f"Задача {self.name} успешно выполнена")
        
        # Вызываем обработчик родительского класса
        super().on_success(retval, task_id, args, kwargs)
    
    def _log_start(self, *args: Any, **kwargs: Any) -> None:
        """
        Логирует начало выполнения задачи.
        
        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        logger.log(
            self.log_level,
            f"Начало выполнения задачи {self.name} "
            f"с аргументами: args={args}, kwargs={kwargs}"
        )
    
    def _log_success(self, *args: Any, **kwargs: Any) -> None:
        """
        Логирует успешное выполнение задачи.
        
        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        logger.log(
            self.log_level,
            f"Задача {self.name} успешно выполнена за {self.duration:.2f} сек."
        )
    
    def _log_error(self, error: Exception, *args: Any, **kwargs: Any) -> None:
        """
        Логирует ошибку выполнения задачи.
        
        Args:
            error: Ошибка.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        logger.error(
            f"Ошибка выполнения задачи {self.name}: {error}\n"
            f"Traceback: {traceback.format_exc()}"
        )
    
    def _send_metrics(self, *args: Any, **kwargs: Any) -> None:
        """
        Отправляет метрики выполнения задачи.
        
        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        # Здесь можно добавить отправку метрик в систему мониторинга
        pass
    
    def _retry(self, error: Exception, *args: Any, **kwargs: Any) -> None:
        """
        Повторяет выполнение задачи.
        
        Args:
            error: Ошибка.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        # Проверяем, нужно ли повторять задачу
        if not self.autoretry_for or not isinstance(error, self.autoretry_for):
            return
        
        # Проверяем, не превышено ли максимальное количество попыток
        if self.retries >= self.max_retries:
            logger.warning(
                f"Превышено максимальное количество попыток выполнения задачи {self.name}: "
                f"{self.retries}/{self.max_retries}"
            )
            return
        
        # Вычисляем задержку перед повторной попыткой
        countdown = self.retry_kwargs.get('countdown', 60)
        
        if self.retry_backoff:
            # Экспоненциальная задержка
            countdown = countdown * (2 ** self.retries)
            
            # Ограничиваем максимальную задержку
            if self.retry_backoff_max:
                countdown = min(countdown, self.retry_backoff_max)
            
            # Добавляем случайное отклонение
            if self.retry_jitter:
                import random
                countdown = countdown + random.uniform(0, countdown * 0.1)
        
        # Повторяем задачу
        self.retry(exc=error, countdown=countdown)


# Регистрируем базовую задачу
app.register_task(BaseTask())

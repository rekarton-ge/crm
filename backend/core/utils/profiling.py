"""
Утилиты для профилирования.

Этот модуль содержит утилиты для профилирования кода.
"""

import cProfile
import functools
import io
import logging
import pstats
import time
from typing import Any, Callable, Dict, List, Optional, Union

from django.conf import settings


logger = logging.getLogger('profiling')


def profile_func(func: Callable) -> Callable:
    """
    Декоратор для профилирования функции.
    
    Args:
        func (Callable): Функция для профилирования.
    
    Returns:
        Callable: Декорированная функция.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Проверяем, включено ли профилирование
        if not getattr(settings, 'ENABLE_PROFILING', False):
            return func(*args, **kwargs)
        
        # Создаем профилировщик
        profiler = cProfile.Profile()
        
        # Запускаем профилировщик
        profiler.enable()
        
        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            return result
        finally:
            # Останавливаем профилировщик
            profiler.disable()
            
            # Получаем статистику
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(30)  # Выводим 30 самых затратных функций
            
            # Логируем статистику
            logger.info(f"Профилирование функции {func.__name__}:\n{s.getvalue()}")
    
    return wrapper


class Timer:
    """
    Класс для измерения времени выполнения кода.
    
    Может использоваться как декоратор или как контекстный менеджер.
    """
    
    def __init__(self, name: Optional[str] = None, log_level: int = logging.INFO):
        """
        Инициализация таймера.
        
        Args:
            name (str, optional): Имя таймера.
            log_level (int, optional): Уровень логирования.
        """
        self.name = name
        self.log_level = log_level
        self.start_time = None
        self.end_time = None
    
    def __call__(self, func: Callable) -> Callable:
        """
        Использование таймера как декоратора.
        
        Args:
            func (Callable): Функция для измерения времени выполнения.
        
        Returns:
            Callable: Декорированная функция.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Проверяем, включено ли профилирование
            if not getattr(settings, 'ENABLE_PROFILING', False):
                return func(*args, **kwargs)
            
            # Запускаем таймер
            self.start()
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                return result
            finally:
                # Останавливаем таймер
                self.stop()
                
                # Логируем время выполнения
                name = self.name or func.__name__
                logger.log(self.log_level, f"Время выполнения {name}: {self.elapsed_time:.6f} сек.")
        
        return wrapper
    
    def __enter__(self) -> 'Timer':
        """
        Вход в контекстный менеджер.
        
        Returns:
            Timer: Экземпляр таймера.
        """
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Выход из контекстного менеджера.
        
        Args:
            exc_type: Тип исключения.
            exc_val: Значение исключения.
            exc_tb: Трассировка исключения.
        """
        self.stop()
        
        # Логируем время выполнения
        name = self.name or 'Блок кода'
        logger.log(self.log_level, f"Время выполнения {name}: {self.elapsed_time:.6f} сек.")
    
    def start(self) -> None:
        """
        Запуск таймера.
        """
        self.start_time = time.time()
    
    def stop(self) -> None:
        """
        Остановка таймера.
        """
        self.end_time = time.time()
    
    @property
    def elapsed_time(self) -> float:
        """
        Возвращает время выполнения в секундах.
        
        Returns:
            float: Время выполнения в секундах.
        """
        if self.start_time is None:
            return 0.0
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time


class MemoryProfiler:
    """
    Класс для профилирования использования памяти.
    
    Может использоваться как декоратор или как контекстный менеджер.
    """
    
    def __init__(self, name: Optional[str] = None, log_level: int = logging.INFO):
        """
        Инициализация профилировщика памяти.
        
        Args:
            name (str, optional): Имя профилировщика.
            log_level (int, optional): Уровень логирования.
        """
        self.name = name
        self.log_level = log_level
        self.start_memory = None
        self.end_memory = None
    
    def __call__(self, func: Callable) -> Callable:
        """
        Использование профилировщика как декоратора.
        
        Args:
            func (Callable): Функция для профилирования использования памяти.
        
        Returns:
            Callable: Декорированная функция.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Проверяем, включено ли профилирование
            if not getattr(settings, 'ENABLE_PROFILING', False):
                return func(*args, **kwargs)
            
            # Запускаем профилировщик
            self.start()
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                return result
            finally:
                # Останавливаем профилировщик
                self.stop()
                
                # Логируем использование памяти
                name = self.name or func.__name__
                logger.log(self.log_level, f"Использование памяти {name}: {self.memory_usage_mb:.2f} МБ")
        
        return wrapper
    
    def __enter__(self) -> 'MemoryProfiler':
        """
        Вход в контекстный менеджер.
        
        Returns:
            MemoryProfiler: Экземпляр профилировщика памяти.
        """
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Выход из контекстного менеджера.
        
        Args:
            exc_type: Тип исключения.
            exc_val: Значение исключения.
            exc_tb: Трассировка исключения.
        """
        self.stop()
        
        # Логируем использование памяти
        name = self.name or 'Блок кода'
        logger.log(self.log_level, f"Использование памяти {name}: {self.memory_usage_mb:.2f} МБ")
    
    def start(self) -> None:
        """
        Запуск профилировщика памяти.
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss
    
    def stop(self) -> None:
        """
        Остановка профилировщика памяти.
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        self.end_memory = process.memory_info().rss
    
    @property
    def memory_usage(self) -> int:
        """
        Возвращает использование памяти в байтах.
        
        Returns:
            int: Использование памяти в байтах.
        """
        if self.start_memory is None:
            return 0
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        end_memory = self.end_memory or process.memory_info().rss
        return end_memory - self.start_memory
    
    @property
    def memory_usage_mb(self) -> float:
        """
        Возвращает использование памяти в мегабайтах.
        
        Returns:
            float: Использование памяти в мегабайтах.
        """
        return self.memory_usage / (1024 * 1024)

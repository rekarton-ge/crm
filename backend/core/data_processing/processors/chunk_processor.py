"""
Модуль для пакетной обработки данных.

Этот модуль содержит классы для эффективной обработки больших наборов данных
путем разделения на небольшие пакеты, что позволяет снизить нагрузку на память
и повысить производительность обработки.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, TypeVar, Union, Type

from django.db import transaction
from django.db.models import Model, QuerySet

from core.data_processing.error_handlers import (
    ErrorCategory,
    ErrorHandler,
    ErrorHandlerFactory,
    ErrorSeverity,
    ProcessingError,
    ProcessingResult
)

# Настройка логгера
logger = logging.getLogger(__name__)

# Типовые переменные для обобщенного программирования
T = TypeVar('T')  # Тип входных данных
R = TypeVar('R')  # Тип результата


class ChunkProcessor(Generic[T, R]):
    """
    Класс для пакетной обработки данных.

    Позволяет эффективно обрабатывать большие наборы данных путем разделения
    на небольшие пакеты и последовательной или параллельной их обработки.
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 use_transactions: bool = True,
                 parallel_processing: bool = False,
                 max_workers: Optional[int] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 show_progress: bool = False,
                 progress_interval: int = 10):
        """
        Инициализирует процессор пакетной обработки с указанными настройками.

        Args:
            chunk_size: Размер пакета данных для обработки.
            use_transactions: Использовать ли транзакции для каждого пакета.
            parallel_processing: Обрабатывать ли пакеты параллельно.
            max_workers: Максимальное количество рабочих потоков при параллельной обработке.
            error_handler: Обработчик ошибок для использования.
            show_progress: Выводить ли информацию о прогрессе обработки.
            progress_interval: Интервал (в процентах) для вывода информации о прогрессе.
        """
        self.chunk_size = chunk_size
        self.use_transactions = use_transactions
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers
        self.error_handler = error_handler or ErrorHandlerFactory.create_default_handler()
        self.show_progress = show_progress
        self.progress_interval = progress_interval

    def get_total_count(self, data: Union[QuerySet, List[T], Iterable[T]]) -> int:
        """
        Получает общее количество элементов в наборе данных.

        Args:
            data: Набор данных для подсчета.

        Returns:
            int: Общее количество элементов.
        """
        if isinstance(data, QuerySet):
            return data.count()
        elif hasattr(data, '__len__'):
            return len(data)
        else:
            # Если не можем определить количество, возвращаем -1
            return -1

    def chunk_data(self, data: Union[QuerySet, List[T], Iterable[T]]) -> Iterable[List[T]]:
        """
        Разделяет набор данных на пакеты.

        Args:
            data: Набор данных для разделения.

        Yields:
            List[T]: Пакет данных.
        """
        if isinstance(data, QuerySet):
            # Для QuerySet используем слайсы
            total_count = data.count()
            for i in range(0, total_count, self.chunk_size):
                yield list(data[i:i + self.chunk_size])
        else:
            # Для других итерируемых объектов
            chunk = []
            for item in data:
                chunk.append(item)
                if len(chunk) >= self.chunk_size:
                    yield chunk
                    chunk = []

            # Возвращаем оставшиеся элементы
            if chunk:
                yield chunk

    def process_chunk(self,
                      chunk: List[T],
                      processor_func: Callable[[T], R],
                      result: ProcessingResult,
                      chunk_index: int) -> List[R]:
        """
        Обрабатывает один пакет данных.

        Args:
            chunk: Пакет данных для обработки.
            processor_func: Функция для обработки каждого элемента.
            result: Результат обработки для обновления.
            chunk_index: Индекс пакета.

        Returns:
            List[R]: Список результатов обработки элементов пакета.
        """
        chunk_results = []

        # Используем транзакцию для пакета, если требуется
        if self.use_transactions:
            try:
                with transaction.atomic():
                    chunk_results = self._process_items(chunk, processor_func, result, chunk_index)

                    # Если есть критические ошибки, откатываем транзакцию
                    if result.has_critical_errors():
                        transaction.set_rollback(True)
                        logger.error(f"Обработка пакета {chunk_index} отменена из-за критических ошибок")
            except Exception as e:
                # Обрабатываем исключение
                self.error_handler.handle_exception(
                    exception=e,
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    context={'chunk_index': chunk_index},
                    result=result
                )
        else:
            # Обработка без транзакции
            chunk_results = self._process_items(chunk, processor_func, result, chunk_index)

        return chunk_results

    def _process_items(self,
                       chunk: List[T],
                       processor_func: Callable[[T], R],
                       result: ProcessingResult,
                       chunk_index: int) -> List[R]:
        """
        Обрабатывает элементы пакета.

        Args:
            chunk: Пакет данных для обработки.
            processor_func: Функция для обработки каждого элемента.
            result: Результат обработки для обновления.
            chunk_index: Индекс пакета.

        Returns:
            List[R]: Список результатов обработки элементов пакета.
        """
        chunk_results = []

        for i, item in enumerate(chunk):
            try:
                # Обработка элемента
                result.processed_count += 1

                # Вызываем функцию обработки
                item_result = processor_func(item)

                # Если функция вернула None, считаем элемент пропущенным
                if item_result is None:
                    result.skipped_count += 1
                else:
                    # Увеличиваем счетчик успешно обработанных
                    result.success_count += 1

                    # Если результат - объект модели, добавляем его в созданные или обновленные
                    if isinstance(item_result, Model):
                        if getattr(item_result, '_state', None) and getattr(item_result._state, 'adding', False):
                            result.created_objects.append(item_result)
                        else:
                            result.updated_objects.append(item_result)

                    # Добавляем результат в список
                    chunk_results.append(item_result)

            except Exception as e:
                # Обрабатываем исключение
                self.error_handler.handle_exception(
                    exception=e,
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.ERROR,
                    context={'chunk_index': chunk_index, 'item_index': i},
                    result=result
                )

                result.skipped_count += 1

        return chunk_results

    def process_data(self, data: Union[QuerySet, List[T], Iterable[T]],
                     processor_func: Callable[[T], R]) -> ProcessingResult:
        """
        Обрабатывает набор данных с использованием указанной функции.

        Args:
            data: Набор данных для обработки.
            processor_func: Функция для обработки каждого элемента.

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        result = ProcessingResult()

        # Получаем общее количество элементов (если возможно)
        total_count = self.get_total_count(data)

        # Инициализируем счетчики для отслеживания прогресса
        processed_chunks = 0
        last_progress = 0
        start_time = time.time()

        # Разделяем данные на пакеты
        chunks = list(self.chunk_data(data))
        total_chunks = len(chunks)

        # Если требуется параллельная обработка
        if self.parallel_processing:
            # Создаем пул потоков для параллельной обработки
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Запускаем задачи обработки пакетов
                future_to_chunk = {
                    executor.submit(self.process_chunk, chunk, processor_func, result, i): i
                    for i, chunk in enumerate(chunks)
                }

                # Обрабатываем результаты по мере их завершения
                for future in as_completed(future_to_chunk):
                    chunk_index = future_to_chunk[future]
                    processed_chunks += 1

                    try:
                        # Получаем результаты обработки пакета
                        future.result()

                        # Отображаем прогресс, если требуется
                        if self.show_progress and total_chunks > 0:
                            progress = (processed_chunks * 100) // total_chunks
                            if progress - last_progress >= self.progress_interval:
                                elapsed_time = time.time() - start_time
                                logger.info(
                                    f"Прогресс: {progress}% ({processed_chunks}/{total_chunks} пакетов, {result.processed_count} элементов, {elapsed_time:.2f} сек)")
                                last_progress = progress

                    except Exception as e:
                        # Обрабатываем исключение выполнения пакета
                        self.error_handler.handle_exception(
                            exception=e,
                            category=ErrorCategory.SYSTEM,
                            severity=ErrorSeverity.CRITICAL,
                            context={'chunk_index': chunk_index},
                            result=result
                        )
        else:
            # Последовательная обработка пакетов
            for i, chunk in enumerate(chunks):
                self.process_chunk(chunk, processor_func, result, i)
                processed_chunks += 1

                # Отображаем прогресс, если требуется
                if self.show_progress and total_chunks > 0:
                    progress = (processed_chunks * 100) // total_chunks
                    if progress - last_progress >= self.progress_interval:
                        elapsed_time = time.time() - start_time
                        logger.info(
                            f"Прогресс: {progress}% ({processed_chunks}/{total_chunks} пакетов, {result.processed_count} элементов, {elapsed_time:.2f} сек)")
                        last_progress = progress

        # Завершающая информация о прогрессе
        if self.show_progress:
            elapsed_time = time.time() - start_time
            logger.info(
                f"Обработка завершена: {result.processed_count} элементов, {result.success_count} успешно, {result.skipped_count} пропущено, {elapsed_time:.2f} сек")

        # Обновляем общий статус обработки
        result.success = not result.has_critical_errors()

        return result

    @classmethod
    def process(cls,
                data: Union[QuerySet, List[T], Iterable[T]],
                processor_func: Callable[[T], R],
                chunk_size: int = 1000,
                use_transactions: bool = True,
                parallel_processing: bool = False,
                **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрой пакетной обработки данных.

        Args:
            data: Набор данных для обработки.
            processor_func: Функция для обработки каждого элемента.
            chunk_size: Размер пакета данных для обработки.
            use_transactions: Использовать ли транзакции для каждого пакета.
            parallel_processing: Обрабатывать ли пакеты параллельно.
            **kwargs: Дополнительные аргументы для конструктора ChunkProcessor.

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        processor = cls(
            chunk_size=chunk_size,
            use_transactions=use_transactions,
            parallel_processing=parallel_processing,
            **kwargs
        )
        return processor.process_data(data, processor_func)


class BulkChunkProcessor(ChunkProcessor[T, R]):
    """
    Класс для пакетной обработки данных с поддержкой массовых операций.

    Расширяет базовый ChunkProcessor дополнительной поддержкой bulk_create,
    bulk_update и других массовых операций для моделей Django.
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 use_transactions: bool = True,
                 parallel_processing: bool = False,
                 max_workers: Optional[int] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 show_progress: bool = False,
                 progress_interval: int = 10,
                 ignore_conflicts: bool = False,
                 update_fields: Optional[List[str]] = None):
        """
        Инициализирует процессор массовой пакетной обработки с указанными настройками.

        Args:
            chunk_size: Размер пакета данных для обработки.
            use_transactions: Использовать ли транзакции для каждого пакета.
            parallel_processing: Обрабатывать ли пакеты параллельно.
            max_workers: Максимальное количество рабочих потоков при параллельной обработке.
            error_handler: Обработчик ошибок для использования.
            show_progress: Выводить ли информацию о прогрессе обработки.
            progress_interval: Интервал (в процентах) для вывода информации о прогрессе.
            ignore_conflicts: Игнорировать ли конфликты при bulk_create.
            update_fields: Список полей для обновления при bulk_update.
        """
        super().__init__(
            chunk_size=chunk_size,
            use_transactions=use_transactions,
            parallel_processing=parallel_processing,
            max_workers=max_workers,
            error_handler=error_handler,
            show_progress=show_progress,
            progress_interval=progress_interval
        )

        self.ignore_conflicts = ignore_conflicts
        self.update_fields = update_fields

    def bulk_create(self, model_class: Type[Model], data: List[Dict[str, Any]]) -> ProcessingResult:
        """
        Массово создает объекты модели из списка словарей.

        Args:
            model_class: Класс модели Django.
            data: Список словарей с данными для создания объектов.

        Returns:
            ProcessingResult: Результат массового создания.
        """
        result = ProcessingResult()

        def create_object(item_data: Dict[str, Any]) -> Model:
            # Создаем экземпляр модели
            instance = model_class(**item_data)
            return instance

        # Обрабатываем данные
        process_result = self.process_data(data, create_object)

        # Если были ошибки, возвращаем результат
        if process_result.errors:
            return process_result

        # Разделяем созданные объекты на пакеты для массового создания
        created_objects = process_result.created_objects
        chunks = [created_objects[i:i + self.chunk_size] for i in range(0, len(created_objects), self.chunk_size)]

        # Инициализируем результат
        bulk_result = ProcessingResult()
        bulk_result.processed_count = len(created_objects)

        # Создаем объекты с использованием bulk_create
        try:
            for chunk in chunks:
                model_class.objects.bulk_create(chunk, ignore_conflicts=self.ignore_conflicts)
                bulk_result.success_count += len(chunk)
                bulk_result.created_objects.extend(chunk)

            bulk_result.success = True

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                result=bulk_result
            )

            bulk_result.success = False

        return bulk_result

    def bulk_update(self, queryset: QuerySet, update_func: Callable[[Model], None]) -> ProcessingResult:
        """
        Массово обновляет объекты модели с использованием функции обновления.

        Args:
            queryset: QuerySet с объектами для обновления.
            update_func: Функция для обновления каждого объекта.

        Returns:
            ProcessingResult: Результат массового обновления.
        """
        result = ProcessingResult()

        # Проверяем, что указаны поля для обновления
        if not self.update_fields:
            error = ProcessingError(
                message="Не указаны поля для обновления (update_fields)",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL
            )
            self.error_handler.handle_error(error, result)
            return result

        # Обрабатываем объекты
        process_result = self.process_data(queryset, update_func)

        # Если были ошибки, возвращаем результат
        if process_result.errors:
            return process_result

        # Разделяем обновленные объекты на пакеты для массового обновления
        updated_objects = process_result.updated_objects
        chunks = [updated_objects[i:i + self.chunk_size] for i in range(0, len(updated_objects), self.chunk_size)]

        # Инициализируем результат
        bulk_result = ProcessingResult()
        bulk_result.processed_count = len(updated_objects)

        # Обновляем объекты с использованием bulk_update
        try:
            model_class = queryset.model

            for chunk in chunks:
                model_class.objects.bulk_update(chunk, self.update_fields)
                bulk_result.success_count += len(chunk)
                bulk_result.updated_objects.extend(chunk)

            bulk_result.success = True

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                result=bulk_result
            )

            bulk_result.success = False

        return bulk_result

    @classmethod
    def bulk_create_from_data(cls,
                              model_class: Type[Model],
                              data: List[Dict[str, Any]],
                              chunk_size: int = 1000,
                              ignore_conflicts: bool = False,
                              **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрого массового создания объектов.

        Args:
            model_class: Класс модели Django.
            data: Список словарей с данными для создания объектов.
            chunk_size: Размер пакета данных для обработки.
            ignore_conflicts: Игнорировать ли конфликты при bulk_create.
            **kwargs: Дополнительные аргументы для конструктора BulkChunkProcessor.

        Returns:
            ProcessingResult: Результат массового создания.
        """
        processor = cls(
            chunk_size=chunk_size,
            ignore_conflicts=ignore_conflicts,
            **kwargs
        )
        return processor.bulk_create(model_class, data)

    @classmethod
    def bulk_update_queryset(cls,
                             queryset: QuerySet,
                             update_func: Callable[[Model], None],
                             update_fields: List[str],
                             chunk_size: int = 1000,
                             **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрого массового обновления объектов.

        Args:
            queryset: QuerySet с объектами для обновления.
            update_func: Функция для обновления каждого объекта.
            update_fields: Список полей для обновления.
            chunk_size: Размер пакета данных для обработки.
            **kwargs: Дополнительные аргументы для конструктора BulkChunkProcessor.

        Returns:
            ProcessingResult: Результат массового обновления.
        """
        processor = cls(
            chunk_size=chunk_size,
            update_fields=update_fields,
            **kwargs
        )
        return processor.bulk_update(queryset, update_func)
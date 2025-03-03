"""
Модуль для потоковой обработки данных.

Этот модуль содержит классы для эффективной потоковой обработки данных,
что позволяет работать с большими объемами данных без загрузки их
полностью в память.
"""

import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, TypeVar, Union

from django.db import transaction

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


class StreamProcessor(Generic[T, R]):
    """
    Класс для потоковой обработки данных.

    Позволяет эффективно обрабатывать потоки данных, где элементы обрабатываются
    по мере поступления, без необходимости загружать весь набор данных в память.
    """

    def __init__(self,
                 buffer_size: int = 100,
                 use_transactions: bool = False,
                 transaction_size: int = 100,
                 parallel_processing: bool = False,
                 max_workers: Optional[int] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 show_progress: bool = False,
                 progress_interval: int = 10):
        """
        Инициализирует процессор потоковой обработки с указанными настройками.

        Args:
            buffer_size: Размер буфера для промежуточных данных.
            use_transactions: Использовать ли транзакции для групп элементов.
            transaction_size: Количество элементов в одной транзакции.
            parallel_processing: Обрабатывать ли элементы параллельно.
            max_workers: Максимальное количество рабочих потоков при параллельной обработке.
            error_handler: Обработчик ошибок для использования.
            show_progress: Выводить ли информацию о прогрессе обработки.
            progress_interval: Интервал (в секундах) для вывода информации о прогрессе.
        """
        self.buffer_size = buffer_size
        self.use_transactions = use_transactions
        self.transaction_size = transaction_size
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers
        self.error_handler = error_handler or ErrorHandlerFactory.create_default_handler()
        self.show_progress = show_progress
        self.progress_interval = progress_interval

        # Внутренние переменные
        self.input_queue = Queue(maxsize=buffer_size)
        self.output_queue = Queue(maxsize=buffer_size)
        self.stop_event = Event()
        self.processor_func = None
        self.result = None

    def process_element(self, item: T) -> Optional[R]:
        """
        Обрабатывает один элемент данных.

        Args:
            item: Элемент данных для обработки.

        Returns:
            Optional[R]: Результат обработки элемента или None, если элемент не обработан.
        """
        try:
            # Обработка элемента
            self.result.processed_count += 1

            # Вызываем функцию обработки
            item_result = self.processor_func(item)

            # Если функция вернула None, считаем элемент пропущенным
            if item_result is None:
                self.result.skipped_count += 1
                return None
            else:
                # Увеличиваем счетчик успешно обработанных
                self.result.success_count += 1
                return item_result

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                context={'item': str(item)[:100]},
                result=self.result
            )

            self.result.skipped_count += 1
            return None

    def producer_thread(self, data_stream: Iterator[T]) -> None:
        """
        Поток для чтения данных из потока и помещения их в очередь.

        Args:
            data_stream: Итератор с данными для обработки.
        """
        try:
            # Читаем данные из потока
            for item in data_stream:
                # Проверяем, не был ли установлен сигнал остановки
                if self.stop_event.is_set():
                    break

                # Помещаем элемент в очередь
                self.input_queue.put(item)

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                result=self.result
            )

        finally:
            # Помечаем, что данные закончились
            self.input_queue.put(None)

    def worker_thread(self) -> None:
        """
        Рабочий поток для обработки элементов из очереди.
        """
        # Если используем транзакции, создаем буфер для элементов в транзакции
        transaction_buffer = []

        try:
            while not self.stop_event.is_set():
                # Получаем элемент из очереди
                try:
                    item = self.input_queue.get(timeout=1)
                except Empty:
                    continue

                # Если получили None, значит поток завершает работу
                if item is None:
                    # Помещаем None обратно для других рабочих потоков
                    self.input_queue.put(None)
                    break

                # Если используем транзакции
                if self.use_transactions:
                    transaction_buffer.append(item)

                    # Если буфер заполнен, обрабатываем его в транзакции
                    if len(transaction_buffer) >= self.transaction_size:
                        self._process_transaction_buffer(transaction_buffer)
                        transaction_buffer = []
                else:
                    # Обрабатываем элемент без транзакции
                    result = self.process_element(item)

                    # Добавляем результат в выходную очередь
                    if result is not None:
                        self.output_queue.put(result)

                # Уведомляем очередь, что элемент обработан
                self.input_queue.task_done()

            # Обрабатываем оставшиеся элементы в буфере транзакции
            if self.use_transactions and transaction_buffer:
                self._process_transaction_buffer(transaction_buffer)

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                result=self.result
            )

            # Останавливаем обработку
            self.stop_event.set()

    def _process_transaction_buffer(self, buffer: List[T]) -> None:
        """
        Обрабатывает буфер элементов в одной транзакции.

        Args:
            buffer: Список элементов для обработки.
        """
        try:
            # Обрабатываем элементы в транзакции
            with transaction.atomic():
                results = []

                for item in buffer:
                    result = self.process_element(item)
                    if result is not None:
                        results.append(result)

                # Если есть критические ошибки, откатываем транзакцию
                if self.result.has_critical_errors():
                    transaction.set_rollback(True)
                    logger.error("Обработка транзакции отменена из-за критических ошибок")
                else:
                    # Добавляем результаты в выходную очередь
                    for result in results:
                        self.output_queue.put(result)

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                result=self.result
            )

    def consumer_thread(self, output_handler: Optional[Callable[[R], None]] = None) -> None:
        """
        Поток для обработки результатов из очереди.

        Args:
            output_handler: Функция для обработки каждого результата.
        """
        try:
            while not self.stop_event.is_set():
                # Получаем результат из очереди
                try:
                    result = self.output_queue.get(timeout=1)
                except Empty:
                    # Если очередь пуста и производитель завершил работу, завершаем работу
                    if self.input_queue.empty() and not self.input_queue.unfinished_tasks:
                        break
                    continue

                # Если есть обработчик результатов, вызываем его
                if output_handler:
                    try:
                        output_handler(result)
                    except Exception as e:
                        # Обрабатываем исключение
                        self.error_handler.handle_exception(
                            exception=e,
                            category=ErrorCategory.UNKNOWN,
                            severity=ErrorSeverity.ERROR,
                            context={'result': str(result)[:100]},
                            result=self.result
                        )

                # Уведомляем очередь, что результат обработан
                self.output_queue.task_done()

        except Exception as e:
            # Обрабатываем исключение
            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                result=self.result
            )

            # Останавливаем обработку
            self.stop_event.set()

    def progress_thread(self, total_count: Optional[int] = None) -> None:
        """
        Поток для отображения прогресса обработки.

        Args:
            total_count: Общее количество элементов (если известно).
        """
        start_time = time.time()
        last_log_time = start_time
        last_processed_count = 0

        try:
            while not self.stop_event.is_set():
                # Спим некоторое время
                time.sleep(0.1)

                # Получаем текущее время
                current_time = time.time()

                # Проверяем, прошло ли достаточно времени для нового вывода
                if current_time - last_log_time >= self.progress_interval:
                    # Получаем текущий прогресс
                    processed_count = self.result.processed_count
                    success_count = self.result.success_count
                    skipped_count = self.result.skipped_count

                    # Рассчитываем скорость обработки
                    elapsed_time = current_time - last_log_time
                    items_per_second = (processed_count - last_processed_count) / elapsed_time

                    # Если известно общее количество, рассчитываем процент и оставшееся время
                    if total_count is not None and total_count > 0:
                        percent = (processed_count * 100) // total_count

                        # Рассчитываем оставшееся время
                        if items_per_second > 0:
                            remaining_items = total_count - processed_count
                            remaining_time = remaining_items / items_per_second

                            # Выводим информацию о прогрессе
                            logger.info(
                                f"Прогресс: {percent}% ({processed_count}/{total_count}, {items_per_second:.2f} эл/сек, осталось {remaining_time:.2f} сек)")
                        else:
                            logger.info(f"Прогресс: {percent}% ({processed_count}/{total_count})")
                    else:
                        # Выводим информацию о прогрессе без процентов
                        logger.info(
                            f"Обработано: {processed_count} элементов ({items_per_second:.2f} эл/сек), успешно: {success_count}, пропущено: {skipped_count}")

                    # Обновляем время последнего вывода и счетчик
                    last_log_time = current_time
                    last_processed_count = processed_count

                # Если обработка завершена, выходим из цикла
                if self.input_queue.empty() and not self.input_queue.unfinished_tasks and self.output_queue.empty():
                    break

        except Exception as e:
            # Обрабатываем исключение
            logger.error(f"Ошибка в потоке прогресса: {str(e)}")

    def process_stream(self,
                       data_stream: Iterator[T],
                       processor_func: Callable[[T], R],
                       output_handler: Optional[Callable[[R], None]] = None,
                       total_count: Optional[int] = None) -> ProcessingResult:
        """
        Обрабатывает поток данных с использованием указанной функции.

        Args:
            data_stream: Итератор с данными для обработки.
            processor_func: Функция для обработки каждого элемента.
            output_handler: Функция для обработки каждого результата.
            total_count: Общее количество элементов (если известно).

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        # Инициализируем результат
        self.result = ProcessingResult()
        self.processor_func = processor_func

        # Сбрасываем сигнал остановки
        self.stop_event.clear()

        # Запускаем поток производителя
        producer = Thread(target=self.producer_thread, args=(data_stream,))
        producer.daemon = True
        producer.start()

        # Запускаем рабочие потоки
        workers = []
        if self.parallel_processing:
            # Создаем пул потоков
            num_workers = self.max_workers or 4
            for _ in range(num_workers):
                worker = Thread(target=self.worker_thread)
                worker.daemon = True
                worker.start()
                workers.append(worker)
        else:
            # Запускаем один рабочий поток
            worker = Thread(target=self.worker_thread)
            worker.daemon = True
            worker.start()
            workers.append(worker)

        # Запускаем поток потребителя
        consumer = Thread(target=self.consumer_thread, args=(output_handler,))
        consumer.daemon = True
        consumer.start()

        # Запускаем поток отображения прогресса, если нужно
        progress_thread = None
        if self.show_progress:
            progress_thread = Thread(target=self.progress_thread, args=(total_count,))
            progress_thread.daemon = True
            progress_thread.start()

        try:
            # Ждем завершения работы всех потоков
            producer.join()

            for worker in workers:
                worker.join()

            consumer.join()

            if progress_thread:
                progress_thread.join()

        except KeyboardInterrupt:
            # Обрабатываем прерывание пользователем
            logger.info("Обработка прервана пользователем")
            self.stop_event.set()

            # Ждем завершения работы всех потоков
            producer.join()

            for worker in workers:
                worker.join()

            consumer.join()

            if progress_thread:
                progress_thread.join()

        # Обновляем общий статус обработки
        self.result.success = not self.result.has_critical_errors()

        # Выводим информацию о результатах
        if self.show_progress:
            elapsed_time = time.time() - producer.start_time if hasattr(producer, 'start_time') else 0
            logger.info(
                f"Обработка завершена: {self.result.processed_count} элементов, {self.result.success_count} успешно, {self.result.skipped_count} пропущено, {elapsed_time:.2f} сек")

        return self.result

    def process_file(self,
                     file_path: str,
                     file_reader: Callable[[str], Iterator[T]],
                     processor_func: Callable[[T], R],
                     output_handler: Optional[Callable[[R], None]] = None,
                     total_count: Optional[int] = None) -> ProcessingResult:
        """
        Обрабатывает файл с использованием указанных функций.

        Args:
            file_path: Путь к файлу для обработки.
            file_reader: Функция для чтения файла и получения итератора.
            processor_func: Функция для обработки каждого элемента.
            output_handler: Функция для обработки каждого результата.
            total_count: Общее количество элементов (если известно).

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        try:
            # Открываем файл и получаем итератор
            data_stream = file_reader(file_path)

            # Обрабатываем поток данных
            return self.process_stream(data_stream, processor_func, output_handler, total_count)

        except Exception as e:
            # Обрабатываем исключение
            result = ProcessingResult()

            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                context={'file_path': file_path},
                result=result
            )

            logger.error(f"Ошибка при обработке файла {file_path}: {str(e)}")

            return result

    @classmethod
    def process(cls,
                data_stream: Iterator[T],
                processor_func: Callable[[T], R],
                buffer_size: int = 100,
                use_transactions: bool = False,
                parallel_processing: bool = False,
                **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрой потоковой обработки данных.

        Args:
            data_stream: Итератор с данными для обработки.
            processor_func: Функция для обработки каждого элемента.
            buffer_size: Размер буфера для промежуточных данных.
            use_transactions: Использовать ли транзакции для групп элементов.
            parallel_processing: Обрабатывать ли элементы параллельно.
            **kwargs: Дополнительные аргументы для конструктора StreamProcessor.

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        processor = cls(
            buffer_size=buffer_size,
            use_transactions=use_transactions,
            parallel_processing=parallel_processing,
            **kwargs
        )
        return processor.process_stream(data_stream, processor_func)


class FileStreamProcessor(StreamProcessor[str, Any]):
    """
    Класс для потоковой обработки файлов по строкам.

    Специализированный класс для построчной обработки текстовых файлов.
    """

    def process_text_file(self,
                          file_path: str,
                          processor_func: Callable[[str], Any],
                          encoding: str = 'utf-8',
                          skip_lines: int = 0,
                          strip_lines: bool = True,
                          skip_empty_lines: bool = True,
                          output_handler: Optional[Callable[[Any], None]] = None) -> ProcessingResult:
        """
        Обрабатывает текстовый файл построчно.

        Args:
            file_path: Путь к файлу для обработки.
            processor_func: Функция для обработки каждой строки.
            encoding: Кодировка файла.
            skip_lines: Количество строк для пропуска с начала файла.
            strip_lines: Удалять ли пробельные символы в начале и конце строк.
            skip_empty_lines: Пропускать ли пустые строки.
            output_handler: Функция для обработки каждого результата.

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        try:
            # Определяем функцию для чтения файла
            def file_reader(file_path: str) -> Iterator[str]:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Пропускаем указанное количество строк
                    for _ in range(skip_lines):
                        next(f, None)

                    # Читаем остальные строки
                    for line in f:
                        # Обрабатываем строку, если нужно
                        if strip_lines:
                            line = line.strip()

                        # Пропускаем пустые строки, если нужно
                        if skip_empty_lines and not line:
                            continue

                        yield line

            # Получаем общее количество строк в файле
            total_count = None
            if self.show_progress:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        total_count = sum(1 for _ in f) - skip_lines

                        # Если пропускаем пустые строки, нужно их исключить из общего количества
                        if skip_empty_lines:
                            # Приблизительная оценка, так как требуется повторное чтение файла
                            pass
                except Exception:
                    # Если не удалось подсчитать количество строк, продолжаем без этой информации
                    pass

            # Обрабатываем файл
            return self.process_file(file_path, file_reader, processor_func, output_handler, total_count)

        except Exception as e:
            # Обрабатываем исключение
            result = ProcessingResult()

            self.error_handler.handle_exception(
                exception=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                context={'file_path': file_path},
                result=result
            )

            logger.error(f"Ошибка при обработке файла {file_path}: {str(e)}")

            return result

    @classmethod
    def process_file(cls,
                     file_path: str,
                     processor_func: Callable[[str], Any],
                     encoding: str = 'utf-8',
                     buffer_size: int = 1000,
                     parallel_processing: bool = False,
                     **kwargs) -> ProcessingResult:
        """
        Статический метод для быстрой обработки текстового файла.

        Args:
            file_path: Путь к файлу для обработки.
            processor_func: Функция для обработки каждой строки.
            encoding: Кодировка файла.
            buffer_size: Размер буфера для промежуточных данных.
            parallel_processing: Обрабатывать ли строки параллельно.
            **kwargs: Дополнительные аргументы для конструктора FileStreamProcessor.

        Returns:
            ProcessingResult: Результат обработки данных.
        """
        processor = cls(
            buffer_size=buffer_size,
            parallel_processing=parallel_processing,
            **kwargs
        )
        return processor.process_text_file(file_path, processor_func, encoding)
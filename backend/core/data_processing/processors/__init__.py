"""
Пакет процессоров данных.

Этот пакет содержит различные процессоры для обработки данных,
включая обработку больших наборов данных по частям и потоковую обработку данных.
"""

from core.data_processing.processors.chunk_processor import ChunkProcessor
from core.data_processing.processors.stream_processor import StreamProcessor

__all__ = [
    'ChunkProcessor',
    'StreamProcessor',
]
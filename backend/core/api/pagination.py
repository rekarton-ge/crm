"""
Классы пагинации для REST API.

Этот модуль предоставляет стандартные классы пагинации, которые используются
в API для ограничения размера результатов и обеспечения удобной навигации.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Стандартная пагинация для API.

    Обеспечивает постраничное разделение результатов с настраиваемым
    размером страницы и стандартным форматом ответа.
    """
    page_size = 20  # Размер страницы по умолчанию
    page_size_query_param = 'page_size'  # Параметр для указания размера страницы в запросе
    max_page_size = 100  # Максимально допустимый размер страницы

    def get_paginated_response(self, data):
        """
        Возвращает ответ с пагинацией в стандартном формате.

        Аргументы:
            data: Данные для включения в ответ.

        Возвращает:
            Response с метаданными пагинации и данными.
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class LargeResultsSetPagination(StandardResultsSetPagination):
    """
    Пагинация для больших наборов данных.

    Используется, когда требуется вернуть больше элементов на странице.
    """
    page_size = 50  # Увеличенный размер страницы по умолчанию
    max_page_size = 200  # Увеличенный максимальный размер страницы


class SmallResultsSetPagination(StandardResultsSetPagination):
    """
    Пагинация для небольших наборов данных.

    Используется, когда требуется вернуть меньше элементов на странице.
    """
    page_size = 10  # Уменьшенный размер страницы по умолчанию


class CustomPagination(PageNumberPagination):
    """
    Кастомная пагинация с расширенными метаданными.

    Включает дополнительные метаданные в ответ, такие как количество страниц
    и номер текущей страницы.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Расширенный ответ с пагинацией, включающий дополнительные метаданные.

        Аргументы:
            data: Данные для включения в ответ.

        Возвращает:
            Response с расширенными метаданными пагинации и данными.
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('current_page', self.page.number),
            ('total_pages', self.page.paginator.num_pages),
            ('page_size', self.get_page_size(self.request)),
            ('results', data)
        ]))
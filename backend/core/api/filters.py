"""
Фильтры для REST API.

Этот модуль содержит базовые классы и утилиты для фильтрации данных в API.
"""

from django_filters import rest_framework as filters
from django.db import models


class CoreFilterSet(filters.FilterSet):
    """
    Базовый класс фильтра для всех API.

    Расширяет стандартный FilterSet из django-filter, добавляя
    дополнительную функциональность и настройки по умолчанию.
    """

    class Meta:
        """
        Мета-класс для определения поведения фильтра по умолчанию.
        """
        filter_overrides = {
            models.CharField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                }
            },
            models.TextField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                }
            },
            models.EmailField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'iexact',
                }
            },
            models.BooleanField: {
                'filter_class': filters.BooleanFilter,
            },
            models.DateField: {
                'filter_class': filters.DateFilter,
            },
            models.DateTimeField: {
                'filter_class': filters.DateTimeFilter,
            },
        }


def create_boolean_filter(field_name, lookup_expr='exact'):
    """
    Создает булевый фильтр для использования в FilterSet.

    Аргументы:
        field_name: Имя поля для фильтрации.
        lookup_expr: Выражение поиска (по умолчанию 'exact').

    Возвращает:
        Экземпляр filters.BooleanFilter.
    """
    return filters.BooleanFilter(
        field_name=field_name,
        lookup_expr=lookup_expr
    )


def create_date_range_filter(field_name):
    """
    Создает набор фильтров для фильтрации по диапазону дат.

    Аргументы:
        field_name: Имя поля даты для фильтрации.

    Возвращает:
        Словарь с фильтрами 'after' и 'before'.
    """
    return {
        f'{field_name}_after': filters.DateFilter(
            field_name=field_name,
            lookup_expr='gte'
        ),
        f'{field_name}_before': filters.DateFilter(
            field_name=field_name,
            lookup_expr='lte'
        ),
    }


def create_choice_filter(field_name, choices, lookup_expr='exact'):
    """
    Создает фильтр выбора для использования в FilterSet.

    Аргументы:
        field_name: Имя поля для фильтрации.
        choices: Список кортежей (value, display_name) для выбора.
        lookup_expr: Выражение поиска (по умолчанию 'exact').

    Возвращает:
        Экземпляр filters.ChoiceFilter.
    """
    return filters.ChoiceFilter(
        field_name=field_name,
        choices=choices,
        lookup_expr=lookup_expr
    )
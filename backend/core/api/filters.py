"""
Фильтры для REST API.

Этот модуль содержит базовые классы и утилиты для фильтрации данных в API.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

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


def create_boolean_filter(field_name: str, lookup_expr: str = 'exact') -> filters.BooleanFilter:
    """
    Создает булевый фильтр для использования в FilterSet.

    Args:
        field_name: Имя поля для фильтрации.
        lookup_expr: Выражение поиска (по умолчанию 'exact').

    Returns:
        filters.BooleanFilter: Экземпляр BooleanFilter для указанного поля.
    """
    return filters.BooleanFilter(
        field_name=field_name,
        lookup_expr=lookup_expr
    )


def create_date_range_filter(field_name: str) -> Dict[str, filters.DateFilter]:
    """
    Создает набор фильтров для фильтрации по диапазону дат.

    Args:
        field_name: Имя поля даты для фильтрации.

    Returns:
        Dict[str, filters.DateFilter]: Словарь с фильтрами 'after' и 'before'.
    """
    return {
        f'{field_name}_after': filters.DateFilter(
            field_name=field_name,
            lookup_expr='gte',
            label=f"{field_name} после"
        ),
        f'{field_name}_before': filters.DateFilter(
            field_name=field_name,
            lookup_expr='lte',
            label=f"{field_name} до"
        ),
    }


def create_choice_filter(field_name: str, choices: List[Tuple[Any, str]],
                        lookup_expr: str = 'exact') -> filters.ChoiceFilter:
    """
    Создает фильтр выбора для использования в FilterSet.

    Args:
        field_name: Имя поля для фильтрации.
        choices: Список кортежей (значение, отображаемое имя) для выбора.
        lookup_expr: Выражение поиска (по умолчанию 'exact').

    Returns:
        filters.ChoiceFilter: Экземпляр ChoiceFilter для указанного поля.
    """
    return filters.ChoiceFilter(
        field_name=field_name,
        choices=choices,
        lookup_expr=lookup_expr
    )


def create_text_filter(field_name: str, lookup_expr: str = 'icontains') -> filters.CharFilter:
    """
    Создает текстовый фильтр для использования в FilterSet.

    Args:
        field_name: Имя поля для фильтрации.
        lookup_expr: Выражение поиска (по умолчанию 'icontains').

    Returns:
        filters.CharFilter: Экземпляр CharFilter для указанного поля.
    """
    return filters.CharFilter(
        field_name=field_name,
        lookup_expr=lookup_expr
    )


def create_number_range_filter(field_name: str) -> Dict[str, Union[filters.NumberFilter, filters.RangeFilter]]:
    """
    Создает набор фильтров для фильтрации по диапазону чисел.

    Args:
        field_name: Имя числового поля для фильтрации.

    Returns:
        Dict[str, Union[filters.NumberFilter, filters.RangeFilter]]: Словарь с фильтрами.
    """
    return {
        f'{field_name}_min': filters.NumberFilter(
            field_name=field_name,
            lookup_expr='gte',
            label=f"Минимальное {field_name}"
        ),
        f'{field_name}_max': filters.NumberFilter(
            field_name=field_name,
            lookup_expr='lte',
            label=f"Максимальное {field_name}"
        ),
        f'{field_name}_range': filters.RangeFilter(
            field_name=field_name,
            label=f"Диапазон {field_name}"
        ),
    }
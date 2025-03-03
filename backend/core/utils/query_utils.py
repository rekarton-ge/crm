"""
Утилиты для работы с запросами к базе данных.

Этот модуль содержит функции для оптимизации и упрощения работы с запросами к базе данных,
включая фильтрацию, сортировку и пагинацию.
"""

from django.db.models import Q, F, Count, Sum, Avg, Max, Min
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate_queryset(queryset, page=1, page_size=10):
    """
    Пагинирует QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet для пагинации.
        page (int, optional): Номер страницы. По умолчанию 1.
        page_size (int, optional): Размер страницы. По умолчанию 10.
    
    Returns:
        tuple: Кортеж из объекта Paginator, объекта Page и списка объектов на текущей странице.
    """
    paginator = Paginator(queryset, page_size)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return paginator, page_obj, page_obj.object_list


def filter_by_date_range(queryset, date_field, start_date=None, end_date=None):
    """
    Фильтрует QuerySet по диапазону дат.
    
    Args:
        queryset (QuerySet): QuerySet для фильтрации.
        date_field (str): Имя поля с датой.
        start_date (date, optional): Начальная дата. По умолчанию None.
        end_date (date, optional): Конечная дата. По умолчанию None.
    
    Returns:
        QuerySet: Отфильтрованный QuerySet.
    """
    filters = {}
    
    if start_date:
        filters[f"{date_field}__gte"] = start_date
    
    if end_date:
        filters[f"{date_field}__lte"] = end_date
    
    if filters:
        return queryset.filter(**filters)
    
    return queryset


def filter_by_text(queryset, search_text, fields):
    """
    Фильтрует QuerySet по текстовому поиску.
    
    Args:
        queryset (QuerySet): QuerySet для фильтрации.
        search_text (str): Текст для поиска.
        fields (list): Список полей для поиска.
    
    Returns:
        QuerySet: Отфильтрованный QuerySet.
    """
    if not search_text or not fields:
        return queryset
    
    q_objects = Q()
    
    for field in fields:
        q_objects |= Q(**{f"{field}__icontains": search_text})
    
    return queryset.filter(q_objects)


def filter_by_related(queryset, related_field, related_ids):
    """
    Фильтрует QuerySet по связанным объектам.
    
    Args:
        queryset (QuerySet): QuerySet для фильтрации.
        related_field (str): Имя поля связи.
        related_ids (list): Список ID связанных объектов.
    
    Returns:
        QuerySet: Отфильтрованный QuerySet.
    """
    if not related_ids:
        return queryset
    
    return queryset.filter(**{f"{related_field}__in": related_ids})


def filter_by_boolean(queryset, field, value):
    """
    Фильтрует QuerySet по булевому полю.
    
    Args:
        queryset (QuerySet): QuerySet для фильтрации.
        field (str): Имя поля.
        value (bool or str): Значение для фильтрации.
    
    Returns:
        QuerySet: Отфильтрованный QuerySet.
    """
    if value is None:
        return queryset
    
    # Преобразуем строковое значение в булево
    if isinstance(value, str):
        value = value.lower() in ('true', 'yes', '1', 'y')
    
    return queryset.filter(**{field: value})


def order_queryset(queryset, order_by=None, default_order=None):
    """
    Сортирует QuerySet.
    
    Args:
        queryset (QuerySet): QuerySet для сортировки.
        order_by (str, optional): Поле для сортировки. По умолчанию None.
        default_order (str, optional): Поле для сортировки по умолчанию. По умолчанию None.
    
    Returns:
        QuerySet: Отсортированный QuerySet.
    """
    if order_by:
        return queryset.order_by(order_by)
    
    if default_order:
        return queryset.order_by(default_order)
    
    return queryset


def annotate_count(queryset, related_field, annotation_name):
    """
    Аннотирует QuerySet количеством связанных объектов.
    
    Args:
        queryset (QuerySet): QuerySet для аннотации.
        related_field (str): Имя поля связи.
        annotation_name (str): Имя аннотации.
    
    Returns:
        QuerySet: Аннотированный QuerySet.
    """
    return queryset.annotate(**{annotation_name: Count(related_field)})


def annotate_sum(queryset, field, annotation_name, default=0):
    """
    Аннотирует QuerySet суммой значений поля.
    
    Args:
        queryset (QuerySet): QuerySet для аннотации.
        field (str): Имя поля.
        annotation_name (str): Имя аннотации.
        default (int, optional): Значение по умолчанию. По умолчанию 0.
    
    Returns:
        QuerySet: Аннотированный QuerySet.
    """
    return queryset.annotate(**{annotation_name: Coalesce(Sum(field), default)})


def annotate_avg(queryset, field, annotation_name, default=0):
    """
    Аннотирует QuerySet средним значением поля.
    
    Args:
        queryset (QuerySet): QuerySet для аннотации.
        field (str): Имя поля.
        annotation_name (str): Имя аннотации.
        default (int, optional): Значение по умолчанию. По умолчанию 0.
    
    Returns:
        QuerySet: Аннотированный QuerySet.
    """
    return queryset.annotate(**{annotation_name: Coalesce(Avg(field), default)})


def get_or_none(model_class, **kwargs):
    """
    Получает объект модели или None, если объект не найден.
    
    Args:
        model_class (Model): Класс модели.
        **kwargs: Параметры для фильтрации.
    
    Returns:
        Model or None: Объект модели или None.
    """
    try:
        return model_class.objects.get(**kwargs)
    except model_class.DoesNotExist:
        return None


def bulk_update_or_create(model_class, objects, lookup_fields, update_fields):
    """
    Обновляет или создает объекты модели.
    
    Args:
        model_class (Model): Класс модели.
        objects (list): Список объектов для обновления или создания.
        lookup_fields (list): Список полей для поиска существующих объектов.
        update_fields (list): Список полей для обновления.
    
    Returns:
        tuple: Кортеж из списков созданных и обновленных объектов.
    """
    created_objects = []
    updated_objects = []
    
    for obj in objects:
        lookup_kwargs = {field: getattr(obj, field) for field in lookup_fields}
        
        try:
            existing_obj = model_class.objects.get(**lookup_kwargs)
            
            # Обновляем существующий объект
            for field in update_fields:
                setattr(existing_obj, field, getattr(obj, field))
            
            existing_obj.save(update_fields=update_fields)
            updated_objects.append(existing_obj)
        
        except model_class.DoesNotExist:
            # Создаем новый объект
            obj.save()
            created_objects.append(obj)
    
    return created_objects, updated_objects

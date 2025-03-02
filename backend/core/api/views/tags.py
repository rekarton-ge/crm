"""
Представления API для работы с тегами.

Этот модуль содержит представления API для управления тегами
и связями объектов с тегами.
"""

from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models.tags import Tag, GenericTaggedItem
from core.api.serializers.tags import (
    TagSerializer,
    TagCreateSerializer,
    TagUpdateSerializer,
    GenericTaggedItemSerializer,
    TaggedItemCreateSerializer,
    TaggedItemDeleteSerializer,
    TagWithObjectCountSerializer,
    ObjectTagsSerializer,
    BulkTagsSerializer
)
from core.api.permissions import ReadOnlyOrAdmin
from core.cache.decorators import cache_response
from core.mixins.view_mixins import LoggingMixin
from core.services.tag_service import TagService


class TagViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    API для работы с тегами.

    Позволяет получать, создавать, обновлять и удалять теги.
    Доступ к изменению тегов имеют только администраторы.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'slug', 'created_at', 'updated_at']
    ordering = ['name']
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Возвращает базовый queryset для тегов.

        В зависимости от действия может быть модифицирован.

        Returns:
            QuerySet: QuerySet для тегов
        """
        queryset = super().get_queryset()

        # Для действия 'popular' добавляем аннотацию с количеством объектов
        if self.action == 'popular':
            queryset = queryset.annotate(objects_count=Count('generic_tagged_items'))

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Класс сериализатора в зависимости от текущего действия.
        """
        if self.action == 'create':
            return TagCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TagUpdateSerializer
        elif self.action == 'popular':
            return TagWithObjectCountSerializer

        return TagSerializer

    def get_object(self):
        """
        Получает объект тега либо по slug (по умолчанию), либо по id.

        Returns:
            Tag: Объект тега
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Проверяем, передан ли slug или id
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg)

        filter_kwargs = {}
        if lookup.isdigit():
            filter_kwargs['id'] = lookup
        else:
            filter_kwargs[self.lookup_field] = lookup

        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)

        return obj

    @cache_response(timeout=300, key_func='get_tags_cache_key')
    def list(self, request, *args, **kwargs):
        """
        Получение списка тегов с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ со списком тегов
        """
        return super().list(request, *args, **kwargs)

    @cache_response(timeout=300, key_func='get_tag_detail_cache_key')
    def retrieve(self, request, *args, **kwargs):
        """
        Получение конкретного тега с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ с данными о теге
        """
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300)
    def popular(self, request):
        """
        Получение популярных тегов.

        Теги сортируются по количеству связанных с ними объектов.

        Args:
            request: HTTP request объект

        Returns:
            Response: HTTP ответ со списком популярных тегов
        """
        # Количество тегов, которые нужно вернуть
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
            if limit <= 0:
                limit = 10
        except ValueError:
            limit = 10

        # Получаем теги, отсортированные по количеству объектов
        queryset = self.get_queryset().order_by('-objects_count')[:limit]
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    @cache_response(timeout=300)
    def objects(self, request, slug=None):
        """
        Получение объектов, связанных с тегом.

        Args:
            request: HTTP request объект
            slug: Slug тега

        Returns:
            Response: HTTP ответ со списком объектов, связанных с тегом
        """
        tag = self.get_object()

        # Получаем тип контента, если он указан в параметрах
        content_type_str = request.query_params.get('content_type', None)
        content_type = None

        if content_type_str:
            try:
                app_label, model = content_type_str.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model)
            except (ValueError, ContentType.DoesNotExist):
                return Response(
                    {"error": "Неверный формат типа контента. Должен быть в формате 'app_label.model'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Получаем связи этого тега с объектами
        tagged_items = GenericTaggedItem.objects.filter(tag=tag)

        # Фильтруем по типу контента, если он указан
        if content_type:
            tagged_items = tagged_items.filter(content_type=content_type)

        # Сериализуем связи
        serializer = GenericTaggedItemSerializer(tagged_items, many=True)

        return Response(serializer.data)

    def get_tags_cache_key(self, view_instance, view_method, request, *args, **kwargs):
        """
        Создает ключ кэша для списка тегов с учетом параметров фильтрации.

        Args:
            view_instance: Экземпляр представления
            view_method: Метод представления
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            str: Ключ кэша
        """
        query_params = request.query_params.copy()
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(query_params.items())])
        return f'tags_list_{query_string}'

    def get_tag_detail_cache_key(self, view_instance, view_method, request, *args, **kwargs):
        """
        Создает ключ кэша для деталей тега.

        Args:
            view_instance: Экземпляр представления
            view_method: Метод представления
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            str: Ключ кэша
        """
        lookup = kwargs.get(self.lookup_url_kwarg or self.lookup_field)
        return f'tag_detail_{lookup}'


class TaggedItemViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    API для работы с связями объектов с тегами.

    Позволяет получать, создавать и удалять связи объектов с тегами.
    """

    queryset = GenericTaggedItem.objects.all()
    serializer_class = GenericTaggedItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tag']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Класс сериализатора в зависимости от текущего действия.
        """
        if self.action == 'create':
            return TaggedItemCreateSerializer
        elif self.action == 'bulk_tag':
            return BulkTagsSerializer
        elif self.action == 'object_tags':
            return ObjectTagsSerializer
        elif self.action == 'remove_tag':
            return TaggedItemDeleteSerializer

        return GenericTaggedItemSerializer

    @action(detail=False, methods=['post'])
    def bulk_tag(self, request):
        """
        Массовое присвоение тегов объекту.

        Args:
            request: HTTP request объект. Должен содержать content_type, object_id и список тегов.

        Returns:
            Response: HTTP ответ с результатом операции
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_type = serializer.validated_data['content_type']
        object_id = serializer.validated_data['object_id']
        tags = serializer.validated_data['tags']

        # Используем сервис для массового присвоения тегов
        tag_service = TagService()
        created, errors = tag_service.bulk_assign_tags(content_type, object_id, tags)

        return Response({
            'message': f'Присвоено тегов: {len(created)}',
            'errors': errors,
            'tagged_items': GenericTaggedItemSerializer(created, many=True).data
        })

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300)
    def object_tags(self, request):
        """
        Получение всех тегов объекта.

        Args:
            request: HTTP request объект. Должен содержать параметры content_type и object_id.

        Returns:
            Response: HTTP ответ со списком тегов объекта
        """
        content_type_str = request.query_params.get('content_type', None)
        object_id = request.query_params.get('object_id', None)

        if not content_type_str or not object_id:
            return Response(
                {"error": "Необходимо указать параметры content_type и object_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            app_label, model = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            return Response(
                {"error": "Неверный формат типа контента. Должен быть в формате 'app_label.model'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем теги объекта
        tagged_items = GenericTaggedItem.objects.filter(
            content_type=content_type,
            object_id=object_id
        )

        tags = [item.tag for item in tagged_items]

        # Используем сериализатор для вывода тегов объекта
        data = {
            'content_type': content_type_str,
            'object_id': object_id,
            'tags': tags
        }

        serializer = ObjectTagsSerializer(data)

        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def remove_tag(self, request):
        """
        Удаление тега у объекта.

        Args:
            request: HTTP request объект. Должен содержать content_type, object_id и tag.

        Returns:
            Response: HTTP ответ с результатом операции
        """
        serializer = TaggedItemDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Получаем связь тега с объектом из валидатора
        tagged_item = serializer.validated_data['tagged_item']

        # Удаляем связь
        tagged_item.delete()

        return Response({
            'message': 'Тег успешно удален у объекта.'
        })
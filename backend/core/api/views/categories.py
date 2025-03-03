"""
Представления API для работы с категориями.

Этот модуль содержит представления API для управления категориями.
"""

from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models.metadata import Category
from core.api.serializers.categories import (
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer
)
from core.api.permissions import ReadOnlyOrAdmin
from core.cache.decorators import cache_response


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API для работы с категориями.

    Позволяет получать, создавать, обновлять и удалять категории.
    Доступ к изменению категорий имеют только администраторы.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'slug', 'created_at', 'updated_at']
    ordering = ['name']
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Возвращает queryset с фильтрацией по удаленным объектам.
        
        Returns:
            QuerySet: Отфильтрованный queryset
        """
        return Category.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Класс сериализатора в зависимости от текущего действия.
        """
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer

        return CategorySerializer

    def get_object(self):
        """
        Получает объект категории либо по slug (по умолчанию), либо по id.

        Returns:
            Category: Объект категории
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Проверяем, передан ли slug или id
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg)

        filter_kwargs = {}
        if lookup and lookup.isdigit():
            filter_kwargs['id'] = lookup
        else:
            filter_kwargs[self.lookup_field] = lookup

        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)

        return obj

    @cache_response(timeout=300)
    def list(self, request, *args, **kwargs):
        """
        Получение списка категорий с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ со списком категорий
        """
        return super().list(request, *args, **kwargs)

    @cache_response(timeout=300)
    def retrieve(self, request, *args, **kwargs):
        """
        Получение конкретной категории с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ с данными о категории
        """
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    @cache_response(timeout=300)
    def subcategories(self, request, slug=None):
        """
        Получение подкатегорий для указанной категории.

        Args:
            request: HTTP request объект
            slug: Slug категории

        Returns:
            Response: HTTP ответ со списком подкатегорий
        """
        category = self.get_object()
        subcategories = Category.objects.filter(parent=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data) 
"""
Представления API для работы с настройками системы.

Этот модуль содержит представления API для управления настройками
системы, включая получение, создание, обновление и удаление настроек.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models.metadata import Setting
from core.models.settings import SystemSetting, UserSetting
from core.api.serializers.settings import (
    SettingSerializer,
    SettingCreateSerializer,
    SettingUpdateSerializer,
    SettingBulkUpdateSerializer,
    SettingCategorySerializer,
    SettingListByCategorySerializer
)
from core.api.permissions import ReadOnlyOrAdmin
from core.cache.decorators import cache_response


class SettingViewSet(viewsets.ModelViewSet):
    """
    API для работы с настройками системы.

    Позволяет получать, создавать, обновлять и удалять настройки системы.
    Доступ к изменению настроек имеют только администраторы.
    """

    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['key']

    def get_queryset(self):
        """
        Возвращает queryset с фильтрацией по удаленным объектам.
        
        Returns:
            QuerySet: Отфильтрованный queryset
        """
        return Setting.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Класс сериализатора в зависимости от текущего действия.
        """
        if self.action == 'create':
            return SettingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SettingUpdateSerializer
        elif self.action == 'bulk_update':
            return SettingBulkUpdateSerializer

        return SettingSerializer

    @cache_response(timeout=300)
    def list(self, request, *args, **kwargs):
        """
        Получение списка настроек с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ со списком настроек
        """
        return super().list(request, *args, **kwargs)

    @cache_response(timeout=300)
    def retrieve(self, request, *args, **kwargs):
        """
        Получение конкретной настройки с кэшированием результата.

        Args:
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ с данными о настройке
        """
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300, key_func='get_settings_by_category_cache_key')
    def by_category(self, request):
        """
        Получение настроек, сгруппированных по категориям.

        Args:
            request: HTTP request объект

        Returns:
            Response: HTTP ответ со списком категорий и их настройками
        """
        # Группируем настройки по категориям
        categories = {}
        settings = self.filter_queryset(self.get_queryset())

        for setting in settings:
            category = setting.category or 'default'
            if category not in categories:
                categories[category] = []
            categories[category].append(setting)

        # Формируем результат
        result = []
        for category, settings_list in categories.items():
            result.append({
                'category': category,
                'settings': SettingSerializer(settings_list, many=True).data
            })

        serializer = SettingListByCategorySerializer({
            'categories': result
        })

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300)
    def by_key(self, request):
        """
        Получение настройки по её ключу.

        Args:
            request: HTTP request объект. Должен содержать параметр 'key'.

        Returns:
            Response: HTTP ответ с данными о настройке или со статусом 404, если настройка не найдена
        """
        key = request.query_params.get('key', None)
        if not key:
            return Response(
                {"error": "Параметр 'key' не указан."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            setting = Setting.objects.get(key=key)
            serializer = self.get_serializer(setting)
            return Response(serializer.data)
        except Setting.DoesNotExist:
            return Response(
                {"error": f"Настройка с ключом '{key}' не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_update(self, request):
        """
        Массовое обновление настроек.

        Args:
            request: HTTP request объект. Должен содержать JSON с ключом 'settings',
                    содержащим список настроек для обновления.

        Returns:
            Response: HTTP ответ с результатом обновления настроек
        """
        serializer = SettingBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_settings = serializer.update(None, serializer.validated_data)
        return Response({
            'message': f'Обновлено настроек: {len(updated_settings)}',
            'settings': SettingSerializer(updated_settings, many=True).data
        })

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300)
    def categories(self, request):
        """
        Получение списка всех категорий настроек.

        Args:
            request: HTTP request объект

        Returns:
            Response: HTTP ответ со списком категорий
        """
        # Получаем уникальные категории
        categories = Setting.objects.values_list('category', flat=True).distinct()
        # Фильтруем None значения и сортируем
        categories = sorted([c for c in categories if c])

        return Response({
            'categories': categories
        })

    @action(detail=False, methods=['get'])
    @cache_response(timeout=300)
    def by_category_name(self, request, category=None):
        """
        Получение настроек по имени категории.

        Args:
            request: HTTP request объект
            category: Имя категории

        Returns:
            Response: HTTP ответ со списком настроек в указанной категории
        """
        if not category:
            category = request.query_params.get('category', None)
            if not category:
                return Response(
                    {"error": "Категория не указана."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        settings = Setting.objects.filter(category=category)
        if not settings.exists():
            return Response(
                {"error": f"Настройки в категории '{category}' не найдены."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SettingSerializer(settings, many=True)
        return Response(serializer.data)

    def get_settings_cache_key(self, view_instance, view_method, request, *args, **kwargs):
        """
        Создает ключ кэша для списка настроек с учетом параметров фильтрации.

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
        return f'settings_list_{query_string}'

    def get_setting_detail_cache_key(self, view_instance, view_method, request, *args, **kwargs):
        """
        Создает ключ кэша для деталей настройки.

        Args:
            view_instance: Экземпляр представления
            view_method: Метод представления
            request: HTTP request объект
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            str: Ключ кэша
        """
        return f'setting_detail_{kwargs.get("pk")}'

    def get_settings_by_category_cache_key(self, view_instance, view_method, request, *args, **kwargs):
        """
        Создает ключ кэша для настроек, сгруппированных по категориям.

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
        return f'settings_by_category_{query_string}'
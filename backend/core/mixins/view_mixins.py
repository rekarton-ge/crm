"""
Миксины для представлений.

Этот модуль содержит миксины для представлений Django и Django REST Framework.
"""

from typing import Any, Dict, List, Optional, Type, Union

from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class MultiSerializerMixin:
    """
    Миксин для использования разных сериализаторов в зависимости от действия.
    
    Позволяет указать разные сериализаторы для разных действий (list, retrieve, create, update).
    """
    
    serializer_classes: Dict[str, Type[Serializer]] = {}
    
    def get_serializer_class(self) -> Type[Serializer]:
        """
        Возвращает класс сериализатора в зависимости от действия.
        
        Returns:
            Type[Serializer]: Класс сериализатора.
        """
        return self.serializer_classes.get(self.action, super().get_serializer_class())


class ReadWriteSerializerMixin:
    """
    Миксин для использования разных сериализаторов для чтения и записи.
    
    Позволяет указать разные сериализаторы для операций чтения (GET) и записи (POST, PUT, PATCH).
    """
    
    read_serializer_class: Optional[Type[Serializer]] = None
    write_serializer_class: Optional[Type[Serializer]] = None
    
    def get_serializer_class(self) -> Type[Serializer]:
        """
        Возвращает класс сериализатора в зависимости от метода запроса.
        
        Returns:
            Type[Serializer]: Класс сериализатора.
        """
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return self.read_serializer_class or super().get_serializer_class()
        return self.write_serializer_class or super().get_serializer_class()


class SoftDeleteViewMixin:
    """
    Миксин для представлений с поддержкой мягкого удаления.
    
    Переопределяет метод destroy для мягкого удаления объектов.
    """
    
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Мягкое удаление объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RestoreViewMixin:
    """
    Миксин для представлений с поддержкой восстановления удаленных объектов.
    
    Добавляет метод restore для восстановления мягко удаленных объектов.
    """
    
    def restore(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Восстановление удаленного объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        instance.restore()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ActivateDeactivateViewMixin:
    """
    Миксин для представлений с поддержкой активации и деактивации объектов.
    
    Добавляет методы activate и deactivate для активации и деактивации объектов.
    """
    
    def activate(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Активация объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        instance.activate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def deactivate(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Деактивация объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        instance.deactivate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class FilterByUserMixin:
    """
    Миксин для фильтрации объектов по пользователю.
    
    Фильтрует объекты по текущему пользователю.
    """
    
    user_field: str = 'user'
    
    def get_queryset(self) -> QuerySet:
        """
        Возвращает QuerySet, отфильтрованный по текущему пользователю.
        
        Returns:
            QuerySet: Отфильтрованный QuerySet.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated:
            return queryset.filter(**{self.user_field: user})
        
        return queryset.none()


class FilterByOwnerMixin:
    """
    Миксин для фильтрации объектов по владельцу.
    
    Фильтрует объекты по владельцу, который может отличаться от текущего пользователя.
    """
    
    owner_field: str = 'owner'
    
    def get_queryset(self) -> QuerySet:
        """
        Возвращает QuerySet, отфильтрованный по владельцу.
        
        Returns:
            QuerySet: Отфильтрованный QuerySet.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated:
            if user.is_staff or user.is_superuser:
                return queryset
            
            return queryset.filter(**{self.owner_field: user})
        
        return queryset.none()


class HistoryViewMixin:
    """
    Миксин для представлений с поддержкой истории изменений.
    
    Добавляет метод history для получения истории изменений объекта.
    """
    
    history_serializer_class: Optional[Type[Serializer]] = None
    
    def get_history_serializer_class(self) -> Type[Serializer]:
        """
        Возвращает класс сериализатора для истории изменений.
        
        Returns:
            Type[Serializer]: Класс сериализатора.
        """
        return self.history_serializer_class or self.get_serializer_class()
    
    def history(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Получение истории изменений объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        
        if not hasattr(instance, 'history'):
            return Response(
                {'detail': 'История изменений не поддерживается для этого объекта.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        history_objects = instance.history.all()
        page = self.paginate_queryset(history_objects)
        
        if page is not None:
            serializer = self.get_history_serializer_class()(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_history_serializer_class()(history_objects, many=True)
        return Response(serializer.data)


class MetadataViewMixin:
    """
    Миксин для представлений с поддержкой метаданных.
    
    Добавляет методы для работы с метаданными объекта.
    """
    
    def get_metadata(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Получение метаданных объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        
        if not hasattr(instance, 'metadata'):
            return Response(
                {'detail': 'Метаданные не поддерживаются для этого объекта.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(instance.metadata)
    
    def update_metadata(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обновление метаданных объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        
        if not hasattr(instance, 'metadata'):
            return Response(
                {'detail': 'Метаданные не поддерживаются для этого объекта.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        metadata = request.data
        
        if not isinstance(metadata, dict):
            return Response(
                {'detail': 'Метаданные должны быть словарем.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.metadata.update(metadata)
        instance.save(update_fields=['metadata'])
        
        return Response(instance.metadata)
    
    def delete_metadata(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Удаление метаданных объекта.
        
        Args:
            request (Request): HTTP запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.
        
        Returns:
            Response: HTTP ответ.
        """
        instance = self.get_object()
        
        if not hasattr(instance, 'metadata'):
            return Response(
                {'detail': 'Метаданные не поддерживаются для этого объекта.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        key = kwargs.get('key')
        
        if key:
            if key in instance.metadata:
                del instance.metadata[key]
                instance.save(update_fields=['metadata'])
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            return Response(
                {'detail': f'Ключ {key} не найден в метаданных.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        instance.metadata = {}
        instance.save(update_fields=['metadata'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)

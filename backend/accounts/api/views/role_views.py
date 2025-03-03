from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role, CustomPermission
from accounts.api.serializers import (
    RoleSerializer, RoleCreateSerializer, RoleUpdateSerializer,
    PermissionSerializer, UserListSerializer
)
from accounts.api.permissions import IsAdminUser, CanManageRoles, IsSuperUser
from accounts.services import PermissionService


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления ролями.
    """
    queryset = Role.objects.all()
    permission_classes = [CanManageRoles]

    def get_serializer_class(self):
        """
        Возвращает соответствующий сериализатор в зависимости от действия.
        """
        if self.action == 'create':
            return RoleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RoleUpdateSerializer
        return RoleSerializer

    def get_permissions(self):
        """
        Возвращает соответствующие разрешения в зависимости от действия.
        """
        if self.action == 'destroy':
            # Удалять роли может только суперпользователь
            return [IsSuperUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Создает новую роль.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем роль через сервис
        role = PermissionService.create_role(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            permissions=serializer.validated_data.get('permissions', [])
        )

        # Сериализуем созданную роль для ответа
        serializer = RoleSerializer(role)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Обновляет роль.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Запрещаем изменение системных ролей
        if instance.is_system and not request.user.is_superuser:
            return Response(
                {"error": _("Системные роли могут изменять только суперпользователи.")},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Обновляем обычные поля
        instance.name = serializer.validated_data.get('name', instance.name)
        instance.description = serializer.validated_data.get('description', instance.description)
        instance.save()

        # Обновляем разрешения, если они были переданы
        if 'permissions' in serializer.validated_data:
            PermissionService.update_role_permissions(
                instance, serializer.validated_data['permissions']
            )

        # Сериализуем обновленную роль для ответа
        serializer = RoleSerializer(instance)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удаляет роль.
        """
        instance = self.get_object()

        # Запрещаем удаление системных ролей
        if instance.is_system:
            return Response(
                {"error": _("Системные роли нельзя удалять.")},
                status=status.HTTP_403_FORBIDDEN
            )

        # Проверяем, есть ли пользователи с этой ролью
        if instance.users.exists():
            return Response(
                {"error": _("Нельзя удалить роль, которая назначена пользователям.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """
        Получает список пользователей с данной ролью.
        """
        instance = self.get_object()

        # Получаем пользователей с данной ролью
        users = instance.users.all()

        # Применяем пагинацию
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)


class PermissionListView(views.APIView):
    """
    Представление для получения списка доступных разрешений.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        Получает список всех разрешений.
        """
        permissions = CustomPermission.objects.all()

        # Получаем параметры фильтрации из запроса
        content_type = request.query_params.get('content_type')
        is_custom = request.query_params.get('is_custom')

        # Применяем фильтры, если они указаны
        if content_type:
            permissions = permissions.filter(content_type__model=content_type)

        if is_custom:
            is_custom_bool = is_custom.lower() == 'true'
            permissions = permissions.filter(is_custom=is_custom_bool)

        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class UserPermissionsView(views.APIView):
    """
    Представление для получения разрешений текущего пользователя.
    """

    def get(self, request, *args, **kwargs):
        """
        Получает список разрешений текущего пользователя.
        """
        # Получаем разрешения пользователя через сервис
        permissions = PermissionService.get_user_permissions(request.user)

        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class CreatePermissionView(views.APIView):
    """
    Представление для создания кастомного разрешения.
    """
    permission_classes = [IsSuperUser]

    def post(self, request, *args, **kwargs):
        """
        Создает новое кастомное разрешение.
        """
        # Проверяем наличие обязательных полей
        if not all(key in request.data for key in ['codename', 'name']):
            return Response(
                {"error": _("Обязательные поля: codename, name")},
                status=status.HTTP_400_BAD_REQUEST
            )

        codename = request.data['codename']
        name = request.data['name']
        description = request.data.get('description', '')

        # Проверяем уникальность кодового имени
        if CustomPermission.objects.filter(codename=codename).exists():
            return Response(
                {"error": _("Разрешение с таким кодовым именем уже существует.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем разрешение через сервис
        permission = PermissionService.create_permission(
            codename=codename,
            name=name,
            description=description
        )

        serializer = PermissionSerializer(permission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
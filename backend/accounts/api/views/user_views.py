from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.api.serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, ProfileSerializer, ProfileUpdateSerializer,
    AvatarUpdateSerializer, RoleAssignmentSerializer
)
from accounts.api.permissions import IsAdminUser, IsOwnerOrAdmin, CanManageUsers
from accounts.services import UserService, PermissionService
from accounts.models import Role

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    """
    queryset = User.objects.all()
    permission_classes = [CanManageUsers]

    def get_serializer_class(self):
        """
        Возвращает соответствующий сериализатор в зависимости от действия.
        """
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_permissions(self):
        """
        Возвращает соответствующие разрешения в зависимости от действия.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        elif self.action in ['create', 'list']:
            return [IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Создает нового пользователя.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Переопределяем метод создания пользователя, чтобы использовать сервис
        validated_data = serializer.validated_data

        # Извлекаем поля, которые нужны для создания пользователя
        roles = validated_data.pop('roles', [])
        password = validated_data.pop('password', None)

        # Создаем пользователя через сервис
        user = UserService.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', None),
            is_active=validated_data.get('is_active', True),
            is_staff=validated_data.get('is_staff', False),
            created_by=request.user,
            roles=roles
        )

        # Сериализуем созданного пользователя для ответа
        serializer = UserDetailSerializer(user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Обновляет данные пользователя.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Обновляем пользователя через сервис
        user = UserService.update_user(
            user=instance,
            updated_by=request.user,
            **serializer.validated_data
        )

        # Сериализуем обновленного пользователя для ответа
        serializer = UserDetailSerializer(user)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Деактивирует пользователя вместо удаления.
        """
        instance = self.get_object()

        # Запрещаем деактивацию суперпользователя
        if instance.is_superuser and not request.user.is_superuser:
            return Response(
                {"error": _("Недостаточно прав для деактивации суперпользователя.")},
                status=status.HTTP_403_FORBIDDEN
            )

        # Деактивируем пользователя через сервис
        UserService.deactivate_user(instance, deactivated_by=request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Активирует пользователя.
        """
        instance = self.get_object()

        # Активируем пользователя через сервис
        UserService.activate_user(instance, activated_by=request.user)

        return Response({"message": _("Пользователь активирован.")})

    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """
        Получает журнал активности пользователя.
        """
        instance = self.get_object()

        # Получаем параметры из запроса
        activity_type = request.query_params.get('activity_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        # Получаем активность через сервис
        activities = UserService.get_user_activity(
            instance,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        return Response(activities)

    @action(detail=True, methods=['post'])
    def roles(self, request, pk=None):
        """
        Назначает роль пользователю.
        """
        instance = self.get_object()

        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_id = serializer.validated_data.get('role')
        expires_at = serializer.validated_data.get('expires_at')

        try:
            role = Role.objects.get(id=role_id)

            # Назначаем роль пользователю через сервис
            assignment = PermissionService.assign_role_to_user(
                user=instance,
                role=role,
                assigned_by=request.user,
                expires_at=expires_at
            )

            serializer = RoleAssignmentSerializer(assignment)
            return Response(serializer.data)

        except Role.DoesNotExist:
            return Response(
                {"error": _("Указанная роль не найдена.")},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'], url_path='roles/(?P<role_id>[^/.]+)')
    def remove_role(self, request, pk=None, role_id=None):
        """
        Отзывает роль у пользователя.
        """
        instance = self.get_object()

        try:
            role = Role.objects.get(id=role_id)

            # Отзываем роль у пользователя через сервис
            success = PermissionService.remove_role_from_user(instance, role)

            if success:
                return Response({"message": _("Роль отозвана у пользователя.")})
            else:
                return Response(
                    {"error": _("Пользователь не имеет указанной роли.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Role.DoesNotExist:
            return Response(
                {"error": _("Указанная роль не найдена.")},
                status=status.HTTP_404_NOT_FOUND
            )


class CurrentUserView(views.APIView):
    """
    Представление для получения и обновления данных текущего пользователя.
    """

    def get(self, request, *args, **kwargs):
        """
        Получает данные текущего пользователя.
        """
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Обновляет данные текущего пользователя.
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Ограничиваем список полей, которые пользователь может изменить у самого себя
        allowed_fields = ['first_name', 'last_name', 'phone_number']
        update_data = {k: v for k, v in serializer.validated_data.items() if k in allowed_fields}

        # Обновляем пользователя через сервис
        user = UserService.update_user(
            user=request.user,
            updated_by=request.user,
            **update_data
        )

        # Сериализуем обновленного пользователя для ответа
        serializer = UserDetailSerializer(user)

        return Response(serializer.data)


class ProfileView(views.APIView):
    """
    Представление для получения и обновления профиля пользователя.
    """

    def get(self, request, *args, **kwargs):
        """
        Получает профиль текущего пользователя.
        """
        profile = request.user.profile
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Обновляет профиль текущего пользователя.
        """
        profile = request.user.profile
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Обновляем профиль через сервис
        updated_profile = UserService.update_profile(
            user=request.user,
            updated_by=request.user,
            **serializer.validated_data
        )

        # Сериализуем обновленный профиль для ответа
        serializer = ProfileSerializer(updated_profile, context={'request': request})

        return Response(serializer.data)


class AvatarUpdateView(views.APIView):
    """
    Представление для обновления аватара пользователя.
    """

    def post(self, request, *args, **kwargs):
        """
        Загружает новый аватар для текущего пользователя.
        """
        profile = request.user.profile
        serializer = AvatarUpdateSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)

        # Сохраняем аватар
        profile.avatar = serializer.validated_data['avatar']
        profile.save()

        # Получаем URL аватара для ответа
        if profile.avatar:
            avatar_url = request.build_absolute_uri(profile.avatar.url)
        else:
            avatar_url = None

        return Response({"avatar": avatar_url})

    def delete(self, request, *args, **kwargs):
        """
        Удаляет аватар текущего пользователя.
        """
        profile = request.user.profile

        if profile.avatar:
            # Сохраняем старый путь для удаления файла
            old_avatar = profile.avatar

            # Удаляем аватар
            profile.avatar = None
            profile.save()

            # Удаляем файл с диска
            old_avatar.delete(save=False)

        return Response({"message": _("Аватар удален.")})
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from accounts.models import CustomPermission, Role


class PermissionService:
    """
    Сервисный класс для проверки и управления разрешениями пользователей.
    """

    @staticmethod
    def check_permission(user, permission_codename):
        """
        Проверяет, имеет ли пользователь указанное разрешение через свои роли.
        """
        # Суперпользователь имеет все разрешения
        if user.is_superuser:
            return True

        # Проверяем наличие разрешения через роли пользователя
        return user.has_permission(permission_codename)

    @staticmethod
    def get_user_permissions(user):
        """
        Возвращает все разрешения пользователя.
        """
        if user.is_superuser:
            # Суперпользователь имеет все разрешения
            return CustomPermission.objects.all()

        # Получаем разрешения из всех ролей пользователя
        return CustomPermission.objects.filter(roles__users=user).distinct()

    @staticmethod
    def get_user_permission_codenames(user):
        """
        Возвращает список кодовых имен разрешений пользователя.
        """
        permissions = PermissionService.get_user_permissions(user)
        return permissions.values_list('codename', flat=True)

    @staticmethod
    def create_permission(codename, name, description='', content_type=None):
        """
        Создает новое разрешение.
        """
        return CustomPermission.get_or_create_permission(
            codename=codename,
            name=name,
            description=description,
            content_type=content_type
        )

    @staticmethod
    def create_model_permissions(model_class, app_label=None):
        """
        Создает стандартный набор разрешений для модели (view, add, change, delete).
        """
        if app_label is None:
            app_label = model_class._meta.app_label

        model_name = model_class._meta.model_name
        content_type = ContentType.objects.get_for_model(model_class)

        permissions = []

        # Создаем стандартные разрешения для модели
        view_perm = PermissionService.create_permission(
            codename=f'view_{model_name}',
            name=f'Can view {model_name}',
            description=f'Позволяет просматривать объекты {model_name}',
            content_type=content_type
        )
        permissions.append(view_perm)

        add_perm = PermissionService.create_permission(
            codename=f'add_{model_name}',
            name=f'Can add {model_name}',
            description=f'Позволяет создавать объекты {model_name}',
            content_type=content_type
        )
        permissions.append(add_perm)

        change_perm = PermissionService.create_permission(
            codename=f'change_{model_name}',
            name=f'Can change {model_name}',
            description=f'Позволяет изменять объекты {model_name}',
            content_type=content_type
        )
        permissions.append(change_perm)

        delete_perm = PermissionService.create_permission(
            codename=f'delete_{model_name}',
            name=f'Can delete {model_name}',
            description=f'Позволяет удалять объекты {model_name}',
            content_type=content_type
        )
        permissions.append(delete_perm)

        return permissions

    @staticmethod
    def create_role(name, description='', permissions=None, is_system=False):
        """
        Создает новую роль с указанными разрешениями.
        """
        with transaction.atomic():
            role = Role.objects.create(
                name=name,
                description=description,
                is_system=is_system
            )

            if permissions:
                role.permissions.set(permissions)

            return role

    @staticmethod
    def update_role_permissions(role, permissions):
        """
        Обновляет разрешения роли.
        """
        with transaction.atomic():
            role.permissions.clear()
            role.permissions.add(*permissions)
            return role

    @staticmethod
    def assign_role_to_user(user, role, assigned_by=None, expires_at=None):
        """
        Назначает роль пользователю.
        """
        from accounts.models import RoleAssignment

        # Проверяем, есть ли уже такое назначение
        assignment, created = RoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'assigned_by': assigned_by,
                'expires_at': expires_at
            }
        )

        if not created:
            # Обновляем существующее назначение
            assignment.assigned_by = assigned_by
            assignment.expires_at = expires_at
            assignment.save()

        return assignment

    @staticmethod
    def remove_role_from_user(user, role):
        """
        Отзывает роль у пользователя.
        """
        from accounts.models import RoleAssignment

        try:
            assignment = RoleAssignment.objects.get(user=user, role=role)
            assignment.delete()
            return True
        except RoleAssignment.DoesNotExist:
            return False
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только администраторам.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsSuperUser(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только суперпользователям.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение, позволяющее владельцу объекта или администратору изменять объект.
    """

    def has_object_permission(self, request, view, obj):
        # Администраторы могут выполнять любые действия
        if request.user.is_staff:
            return True

        # Проверяем, является ли пользователь владельцем объекта
        # Объект должен иметь атрибут, указывающий на владельца
        return hasattr(obj, 'user') and obj.user == request.user


class HasPermission(permissions.BasePermission):
    """
    Разрешение, проверяющее наличие определенного разрешения у пользователя.
    """

    def __init__(self, permission_codename):
        self.permission_codename = permission_codename

    def has_permission(self, request, view):
        # Проверяем, имеет ли пользователь нужное разрешение
        from accounts.services.permission_service import PermissionService
        return PermissionService.check_permission(request.user, self.permission_codename)


class HasRole(permissions.BasePermission):
    """
    Разрешение, проверяющее наличие определенной роли у пользователя.
    """

    def __init__(self, role_name):
        self.role_name = role_name

    def has_permission(self, request, view):
        # Проверяем, имеет ли пользователь нужную роль
        return request.user.has_role(self.role_name)


class CanManageUsers(permissions.BasePermission):
    """
    Разрешение для управления пользователями.
    """

    def has_permission(self, request, view):
        # Суперпользователи и администраторы могут управлять пользователями
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Также проверяем специальное разрешение
        return request.user.has_permission('manage_users')

    def has_object_permission(self, request, view, obj):
        # Запрещаем администраторам редактировать суперпользователей
        if obj.is_superuser and not request.user.is_superuser:
            return False

        # Запрещаем пользователям редактировать администраторов
        if obj.is_staff and not (request.user.is_staff or request.user.is_superuser):
            return False

        # Пользователь может редактировать свои данные
        if obj == request.user:
            return True

        # Разрешаем доступ администраторам и пользователям с правом управления
        return request.user.is_staff or request.user.has_permission('manage_users')


class CanManageRoles(permissions.BasePermission):
    """
    Разрешение для управления ролями.
    """

    def has_permission(self, request, view):
        # Суперпользователи и администраторы могут управлять ролями
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Также проверяем специальное разрешение
        return request.user.has_permission('manage_roles')

    def has_object_permission(self, request, view, obj):
        # Запрещаем редактировать системные роли всем, кроме суперпользователей
        if obj.is_system and not request.user.is_superuser:
            return False

        # Разрешаем доступ администраторам и пользователям с правом управления
        return request.user.is_staff or request.user.has_permission('manage_roles')
"""
Классы разрешений для REST API.

Этот модуль предоставляет базовые классы разрешений для контроля
доступа к API-эндпоинтам на основе различных критериев.
"""

from rest_framework import permissions


class IsAdminUser(permissions.IsAdminUser):
    """
    Разрешение, которое предоставляет доступ только администраторам.

    Расширяет стандартное разрешение IsAdminUser из DRF.
    """
    message = 'Доступ разрешен только администраторам.'


class IsAuthenticated(permissions.IsAuthenticated):
    """
    Разрешение, которое предоставляет доступ только авторизованным пользователям.

    Расширяет стандартное разрешение IsAuthenticated из DRF.
    """
    message = 'Для выполнения этого действия необходима авторизация.'


class ReadOnly(permissions.BasePermission):
    """
    Разрешение, которое предоставляет доступ только для чтения.

    Позволяет выполнять только безопасные методы (GET, HEAD, OPTIONS).
    """
    message = 'Доступ только для чтения.'

    def has_permission(self, request, view):
        """
        Проверяет, разрешен ли запрос.

        Разрешает только безопасные HTTP-методы.

        Аргументы:
            request: Объект запроса.
            view: Представление API.

        Возвращает:
            True, если метод запроса безопасный, иначе False.
        """
        return request.method in permissions.SAFE_METHODS


class IsOwner(permissions.BasePermission):
    """
    Разрешение, которое проверяет, является ли пользователь владельцем объекта.

    Требует, чтобы у объекта было поле 'user' или 'owner', указывающее на владельца.
    """
    message = 'Вы не являетесь владельцем этого объекта.'

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, имеет ли пользователь разрешение на доступ к объекту.

        Аргументы:
            request: Объект запроса.
            view: Представление API.
            obj: Объект, к которому осуществляется доступ.

        Возвращает:
            True, если пользователь является владельцем объекта, иначе False.
        """
        # Безопасные методы могут быть разрешены отдельно
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверка владельца
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Разрешение, которое предоставляет полный доступ администраторам и доступ только
    для чтения остальным аутентифицированным пользователям.
    Неаутентифицированные пользователи не имеют доступа.
    """
    message = 'Требуются права администратора для изменения данных или аутентификация для чтения.'

    def has_permission(self, request, view):
        """
        Проверяет, разрешен ли запрос.

        Аргументы:
            request: Объект запроса.
            view: Представление API.

        Возвращает:
            True, если пользователь аутентифицирован и метод запроса безопасный,
            или пользователь администратор, иначе False.
        """
        # Проверяем, аутентифицирован ли пользователь
        if not request.user or not request.user.is_authenticated:
            return False

        # Для безопасных методов разрешаем доступ аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для небезопасных методов требуем права администратора
        return request.user.is_staff


class ActionBasedPermission(permissions.BasePermission):
    """
    Разрешение на основе действий (action) в ViewSet.

    Позволяет определить разные разрешения для разных действий в ViewSet.
    """

    def __init__(self):
        self.action_permissions = {}

    def has_permission(self, request, view):
        """
        Проверяет разрешение на основе текущего действия.

        Аргументы:
            request: Объект запроса.
            view: Представление API.

        Возвращает:
            Результат проверки соответствующего разрешения для текущего действия.
        """
        for klass, actions in self.action_permissions.items():
            if view.action in actions:
                return klass().has_permission(request, view)
        return True

    def has_object_permission(self, request, view, obj):
        """
        Проверяет разрешение для объекта на основе текущего действия.

        Аргументы:
            request: Объект запроса.
            view: Представление API.
            obj: Объект, к которому осуществляется доступ.

        Возвращает:
            Результат проверки соответствующего разрешения для текущего действия.
        """
        for klass, actions in self.action_permissions.items():
            if view.action in actions:
                return klass().has_object_permission(request, view, obj)
        return True
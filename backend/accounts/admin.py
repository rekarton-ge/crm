from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    User, Profile, Role, RoleAssignment, CustomPermission,
    UserSession, LoginAttempt, UserActivity
)


class ProfileInline(admin.StackedInline):
    """
    Встроенная форма для профиля пользователя.
    """
    model = Profile
    can_delete = False
    verbose_name_plural = _('Профиль')


class RoleAssignmentInline(admin.TabularInline):
    """
    Встроенная форма для назначения ролей пользователю.
    """
    model = RoleAssignment
    extra = 1
    verbose_name_plural = _('Роли')
    autocomplete_fields = ['role', 'assigned_by']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Административный интерфейс для модели пользователя.
    """
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Права доступа'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
        (_('Безопасность'), {'fields': ('failed_login_attempts', 'last_failed_login', 'account_locked_until')}),
    )

    inlines = [ProfileInline, RoleAssignmentInline]
    readonly_fields = ('date_joined', 'last_login', 'failed_login_attempts',
                       'last_failed_login', 'account_locked_until')

    actions = ['activate_users', 'deactivate_users', 'unlock_users']

    def activate_users(self, request, queryset):
        """
        Активирует выбранных пользователей.
        """
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} пользователей было активировано.'))

    activate_users.short_description = _('Активировать выбранных пользователей')

    def deactivate_users(self, request, queryset):
        """
        Деактивирует выбранных пользователей.
        """
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} пользователей было деактивировано.'))

    deactivate_users.short_description = _('Деактивировать выбранных пользователей')

    def unlock_users(self, request, queryset):
        """
        Разблокирует выбранных пользователей.
        """
        for user in queryset:
            user.unlock_account()

        self.message_user(request, _(f'{queryset.count()} пользователей было разблокировано.'))

    unlock_users.short_description = _('Разблокировать выбранных пользователей')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели роли.
    """
    list_display = ('name', 'description', 'is_system', 'get_permissions_count', 'get_users_count')
    list_filter = ('is_system',)
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('is_system',)

    def get_permissions_count(self, obj):
        """
        Возвращает количество разрешений для отображения в списке.
        """
        return obj.permissions.count()

    get_permissions_count.short_description = _('Разрешения')

    def get_users_count(self, obj):
        """
        Возвращает количество пользователей с ролью для отображения в списке.
        """
        return obj.users.count()

    get_users_count.short_description = _('Пользователи')


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели разрешения.
    """
    list_display = ('codename', 'name', 'content_type', 'is_custom')
    list_filter = ('is_custom', 'content_type')
    search_fields = ('codename', 'name', 'description')
    readonly_fields = ('is_custom',)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели сессии пользователя.
    """
    list_display = ('user', 'device_type', 'ip_address', 'started_at', 'last_activity', 'is_active')
    list_filter = ('device_type', 'started_at', 'last_activity')
    search_fields = ('user__username', 'ip_address', 'session_key')
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent',
                       'device_type', 'location', 'started_at', 'last_activity')

    def is_active(self, obj):
        """
        Проверяет, активна ли сессия.
        """
        return obj.is_active()

    is_active.boolean = True
    is_active.short_description = _('Активна')

    def has_add_permission(self, request):
        """
        Запрещает создание сессий через админку.
        """
        return False


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели попытки входа.
    """
    list_display = ('username', 'ip_address', 'timestamp', 'was_successful', 'failure_reason')
    list_filter = ('was_successful', 'timestamp', 'failure_reason')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('username', 'ip_address', 'user_agent', 'timestamp',
                       'was_successful', 'failure_reason')

    def has_add_permission(self, request):
        """
        Запрещает создание попыток входа через админку.
        """
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели активности пользователя.
    """
    list_display = ('user', 'activity_type', 'description', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'description', 'ip_address', 'object_type', 'object_id')
    readonly_fields = ('user', 'session', 'activity_type', 'description',
                       'timestamp', 'ip_address', 'object_type', 'object_id')

    def has_add_permission(self, request):
        """
        Запрещает создание активностей через админку.
        """
        return False
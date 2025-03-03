"""
Административная панель для модуля Core.

Этот модуль содержит настройки административной панели для модуля Core.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models import (
    Tag, TaggedItem, Setting, Category, AuditLog, LoginAttempt,
    TemplateCategory, Template, TemplateVersion, NotificationChannel,
    NotificationType, Notification, UserNotificationPreference,
    SystemSetting, UserSetting, Theme, TagGroup
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Tag.
    """
    list_display = ('name', 'slug', 'color', 'group', 'created_at', 'is_deleted')
    list_filter = ('group', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'color', 'group')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(TagGroup)
class TagGroupAdmin(admin.ModelAdmin):
    """
    Административная панель для модели TagGroup.
    """
    list_display = ('name', 'slug', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    """
    Административная панель для модели TaggedItem.
    """
    list_display = ('tag', 'content_type', 'object_id', 'created_at', 'is_deleted')
    list_filter = ('tag', 'content_type', 'is_deleted', 'created_at')
    search_fields = ('tag__name', 'object_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('tag', 'content_type', 'object_id')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Setting.
    """
    list_display = ('key', 'is_public', 'created_at', 'is_deleted')
    list_filter = ('is_public', 'is_deleted', 'created_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'is_public')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Category.
    """
    list_display = ('name', 'slug', 'parent', 'created_at', 'is_deleted')
    list_filter = ('parent', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Административная панель для модели AuditLog.
    """
    list_display = ('action', 'user', 'content_type', 'object_id', 'created_at')
    list_filter = ('action', 'user', 'content_type', 'created_at')
    search_fields = ('user__username', 'object_id', 'object_repr', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'action', 'content_type', 'object_id', 'object_repr', 'data')
        }),
        (_('Техническая информация'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Административная панель для модели LoginAttempt.
    """
    list_display = ('username', 'status', 'user', 'ip_address', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('username', 'user__username', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('username', 'status', 'user')
        }),
        (_('Техническая информация'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    """
    Административная панель для модели TemplateCategory.
    """
    list_display = ('name', 'slug', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Template.
    """
    list_display = ('name', 'slug', 'type', 'category', 'is_active', 'created_at', 'is_deleted')
    list_filter = ('type', 'category', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description', 'subject', 'content')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'category', 'type')
        }),
        (_('Содержимое'), {
            'fields': ('subject', 'content', 'variables')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
    """
    Административная панель для модели TemplateVersion.
    """
    list_display = ('template', 'version', 'is_active', 'created_at', 'is_deleted')
    list_filter = ('template', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('template__name', 'subject', 'content')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('template', 'version')
        }),
        (_('Содержимое'), {
            'fields': ('subject', 'content', 'variables')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """
    Административная панель для модели NotificationChannel.
    """
    list_display = ('name', 'slug', 'is_active', 'created_at', 'is_deleted')
    list_filter = ('is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    """
    Административная панель для модели NotificationType.
    """
    list_display = ('name', 'slug', 'template', 'is_active', 'created_at', 'is_deleted')
    list_filter = ('template', 'channels', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Связи'), {
            'fields': ('template', 'channels')
        }),
        (_('Настройки'), {
            'fields': ('is_active',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Notification.
    """
    list_display = ('title', 'user', 'notification_type', 'channel', 'status', 'created_at', 'is_deleted')
    list_filter = ('notification_type', 'channel', 'status', 'is_deleted', 'created_at')
    search_fields = ('title', 'content', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'read_at', 'sent_at', 'delivered_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'channel', 'title', 'content')
        }),
        (_('Статус'), {
            'fields': ('status', 'read_at', 'sent_at', 'delivered_at')
        }),
        (_('Связи'), {
            'fields': ('content_type', 'object_id', 'data')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Административная панель для модели UserNotificationPreference.
    """
    list_display = ('user', 'notification_type', 'channel', 'is_enabled', 'created_at', 'is_deleted')
    list_filter = ('notification_type', 'channel', 'is_enabled', 'is_deleted', 'created_at')
    search_fields = ('user__username', 'notification_type__name', 'channel__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'channel', 'is_enabled')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """
    Административная панель для модели SystemSetting.
    """
    list_display = ('key', 'group', 'is_public', 'is_editable', 'created_at', 'is_deleted')
    list_filter = ('group', 'is_public', 'is_editable', 'is_deleted', 'created_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'group')
        }),
        (_('Настройки'), {
            'fields': ('is_public', 'is_editable')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    """
    Административная панель для модели UserSetting.
    """
    list_display = ('user', 'key', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('user__username', 'key')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'key', 'value')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    """
    Административная панель для модели Theme.
    """
    list_display = ('name', 'slug', 'is_default', 'is_active', 'created_at', 'is_deleted')
    list_filter = ('is_default', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'colors')
        }),
        (_('Настройки'), {
            'fields': ('is_default', 'is_active')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted')
        }),
    )

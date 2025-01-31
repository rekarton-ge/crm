from django.contrib import admin
from .models import Contract, Specification, Invoice, UPD

# Регистрация модели Contract
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'client', 'date', 'status')  # Поля, отображаемые в списке
    list_filter = ('status', 'client')  # Фильтры в админке
    search_fields = ('number', 'name')  # Поиск по номеру и имени договора
    readonly_fields = ('change_history',)  # Поле change_history только для чтения

    # Настройка действий в админке
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Кастомное действие для удаления выбранных объектов
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные договоры"


# Регистрация модели Specification
@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('number', 'contract', 'client', 'date', 'total_amount')  # Поля, отображаемые в списке
    list_filter = ('contract', 'client')  # Фильтры в админке
    search_fields = ('number',)  # Поиск по номеру спецификации
    readonly_fields = ('change_history',)  # Поле change_history только для чтения

    # Настройка действий в админке
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Кастомное действие для удаления выбранных объектов
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные спецификации"


# Регистрация модели Invoice
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'client', 'contract', 'specification', 'date', 'status')  # Поля, отображаемые в списке
    list_filter = ('status', 'client', 'contract')  # Фильтры в админке
    search_fields = ('number',)  # Поиск по номеру счета
    readonly_fields = ('change_history',)  # Поле change_history только для чтения

    # Настройка действий в админке
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Кастомное действие для удаления выбранных объектов
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные счета"


# Регистрация модели UPD
@admin.register(UPD)
class UPDAdmin(admin.ModelAdmin):
    list_display = ('number', 'client', 'contract', 'specification', 'invoice', 'date', 'status')  # Поля, отображаемые в списке
    list_filter = ('status', 'client', 'contract', 'specification')  # Фильтры в админке
    search_fields = ('number',)  # Поиск по номеру УПД
    readonly_fields = ('change_history',)  # Поле change_history только для чтения

    # Настройка действий в админке
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Кастомное действие для удаления выбранных объектов
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные УПД"
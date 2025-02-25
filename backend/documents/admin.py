from django.contrib import admin
from .models import Contract, Specification, Invoice, UPD

# Регистрация модели Contract
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'client', 'date', 'status')
    list_filter = ('status', 'client')
    search_fields = ('number', 'name')
    readonly_fields = ('change_history',)
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные договоры"


# Регистрация модели Specification
@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('number', 'contract', 'client', 'date', 'total_amount')
    list_filter = ('contract', 'client')
    search_fields = ('number',)
    readonly_fields = ('change_history',)
    actions = ['delete_selected']

    # Динамическая фильтрация договоров по клиенту
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "contract":
            # Если объект уже существует (редактирование)
            if request.resolver_match.kwargs.get('object_id'):
                specification = Specification.objects.get(pk=request.resolver_match.kwargs['object_id'])
                kwargs["queryset"] = Contract.objects.filter(client=specification.client)
            # Если объект новый (создание), фильтруем по клиенту из формы
            elif request.method == "POST" and "client" in request.POST:
                client_id = request.POST.get("client")
                if client_id:
                    kwargs["queryset"] = Contract.objects.filter(client_id=client_id)
            else:
                # Если клиент еще не выбран, показываем пустой queryset
                kwargs["queryset"] = Contract.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные спецификации"


# Регистрация модели Invoice
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'client', 'contract', 'specification', 'date', 'status')
    list_filter = ('status', 'client', 'contract')
    search_fields = ('number',)
    readonly_fields = ('change_history',)
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные счета"


# Регистрация модели UPD
@admin.register(UPD)
class UPDAdmin(admin.ModelAdmin):
    list_display = ('number', 'client', 'contract', 'specification', 'invoice', 'date', 'status')
    list_filter = ('status', 'client', 'contract', 'specification')
    search_fields = ('number',)
    readonly_fields = ('change_history',)
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Удалить выбранные УПД"
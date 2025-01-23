from django.contrib import admin
from .models import Client, ClientGroup, Tag  # ✅ Вернули импорты

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "client_type", "email", "phone", "fact_address", "inn", "created_at"]
    search_fields = ["name", "email", "phone", "legal_address", "fact_address", "inn", "ogrn", "bik"]
    list_filter = ["client_type", "group", "created_at"]

# ✅ Добавляем регистрацию моделей
@admin.register(ClientGroup)
class ClientGroupAdmin(admin.ModelAdmin):
    list_display = ["name"]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
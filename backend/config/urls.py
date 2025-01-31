from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('clients.urls')), # Подключаем маршруты из приложения clients
    path('api/documents/', include('documents.urls')),  # Подключаем маршруты из приложения documents
]


# ✅ Добавляем обработку загруженных файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


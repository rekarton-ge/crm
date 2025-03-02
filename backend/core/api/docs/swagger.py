"""
Интеграция со Swagger/OpenAPI.

Этот модуль предоставляет инструменты для генерации и отображения
документации API в формате Swagger/OpenAPI.
"""

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, re_path
from django.conf import settings

from .schema_generator import CoreSchemaGenerator


def get_swagger_view():
    """
    Создает и возвращает представление Swagger для документации API.

    Возвращает:
        SchemaView: Представление документации API.
    """
    schema_view = get_schema_view(
        openapi.Info(
            title="CRM API",
            default_version='v1',
            description="API для CRM-системы",
            terms_of_service="https://www.example.com/terms/",
            contact=openapi.Contact(email="contact@example.com"),
            license=openapi.License(name="Proprietary License"),
        ),
        public=True,
        permission_classes=(permissions.IsAuthenticated,),
        generator_class=CoreSchemaGenerator,
    )
    return schema_view


class SwaggerUISettings:
    """
    Настройки для отображения Swagger UI.
    """

    # Настройки UI по умолчанию
    DEFAULT_SETTINGS = {
        'deepLinking': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'defaultModelRendering': 'model',
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'supportedSubmitMethods': [
            'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'
        ],
    }

    @classmethod
    def get_settings(cls):
        """
        Возвращает настройки Swagger UI.

        Возвращает:
            dict: Настройки Swagger UI.
        """
        # Объединение настроек по умолчанию с настройками из settings.py
        ui_settings = cls.DEFAULT_SETTINGS.copy()
        custom_settings = getattr(settings, 'SWAGGER_UI_SETTINGS', {})
        ui_settings.update(custom_settings)
        return ui_settings


def get_swagger_urls():
    """
    Возвращает список URL-шаблонов для Swagger UI.

    Возвращает:
        list: Список шаблонов URL.
    """
    schema_view = get_swagger_view()
    return [
        re_path(
            r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'
        ),
        path(
            'swagger/',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'
        ),
        path(
            'redoc/',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'
        ),
    ]


def setup_swagger(urlpatterns):
    """
    Настраивает URL-маршруты для Swagger UI.

    Аргументы:
        urlpatterns: Существующие URL-шаблоны.

    Возвращает:
        list: Обновленный список URL-шаблонов.
    """
    # Добавляем URL только для не-продакшн окружений или если явно разрешено
    if settings.DEBUG or getattr(settings, 'ENABLE_SWAGGER_IN_PRODUCTION', False):
        swagger_urls = get_swagger_urls()
        urlpatterns.extend(swagger_urls)

    return urlpatterns


# Функция для настройки Swagger UI в представлении
def setup_swagger_view(schema_view):
    """
    Настраивает представление Swagger с кастомными настройками UI.

    Аргументы:
        schema_view: Исходное представление схемы API.

    Возвращает:
        SchemaView: Настроенное представление схемы API.
    """
    ui_settings = SwaggerUISettings.get_settings()
    schema_view.get_renderer_context = lambda: {
        'swagger_settings': {
            'SECURITY_DEFINITIONS': {
                'Bearer': {
                    'type': 'apiKey',
                    'name': 'Authorization',
                    'in': 'header',
                    'description': 'JWT токен в формате: "Bearer {token}"'
                }
            },
            'USE_SESSION_AUTH': False,
            'VALIDATOR_URL': None,
            'OPERATIONS_SORTER': 'alpha',
            'TAGS_SORTER': 'alpha',
            'DOC_EXPANSION': ui_settings.get('docExpansion', 'list'),
            'DEFAULT_MODEL_RENDERING': ui_settings.get('defaultModelRendering', 'model'),
            'DEFAULT_MODEL_DEPTH': ui_settings.get('defaultModelDepth', -1),
            'SHOW_EXTENSIONS': ui_settings.get('showExtensions', True),
            'SHOW_COMMON_EXTENSIONS': ui_settings.get('showCommonExtensions', True),
            'SUPPORTED_SUBMIT_METHODS': ui_settings.get('supportedSubmitMethods', [
                'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'
            ]),
            'PERSIST_AUTH': ui_settings.get('persistAuth', True),
        }
    }
    return schema_view
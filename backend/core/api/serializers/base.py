"""
Базовые сериализаторы для API.

Этот модуль предоставляет базовые классы сериализаторов, которые используются
во всех API приложения для стандартизации формата вывода и обработки общих случаев.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.settings import api_settings


class BaseSerializer(serializers.Serializer):
    """
    Базовый сериализатор с общими методами и атрибутами для всех сериализаторов.

    Предоставляет общую функциональность для всех сериализаторов,
    включая обработку ошибок и стандартные форматы вывода.
    """

    def to_representation(self, instance):
        """
        Переопределение метода для возможной модификации представления объекта.

        Args:
            instance: Объект для сериализации.

        Returns:
            dict: Сериализованное представление объекта.
        """
        representation = super().to_representation(instance)
        return representation

    def get_attribute(self, instance):
        """
        Переопределение метода для безопасного получения атрибутов объекта.

        Позволяет избежать ошибок при отсутствии атрибутов объекта.

        Args:
            instance: Объект для получения атрибута.

        Returns:
            object: Значение атрибута или None, если атрибут отсутствует.
        """
        try:
            return super().get_attribute(instance)
        except (AttributeError, KeyError, ObjectDoesNotExist):
            return None


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для моделей с общими методами и атрибутами.

    Предоставляет общую функциональность для всех сериализаторов моделей,
    включая обработку ошибок и стандартные форматы вывода.
    """

    class Meta:
        """
        Метакласс для настройки сериализатора.
        """
        abstract = True
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """
        Переопределение метода для возможной модификации представления объекта.

        Args:
            instance: Объект для сериализации.

        Returns:
            dict: Сериализованное представление объекта.
        """
        representation = super().to_representation(instance)
        return representation


class BaseReadOnlyModelSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для отображения моделей без возможности изменения.

    Используется для представления моделей в API без возможности их создания,
    изменения или удаления через сериализатор.
    """

    class Meta:
        """
        Метакласс для настройки сериализатора.
        """
        abstract = True
        read_only_fields = ['__all__']


class ContentTypeField(serializers.Field):
    """
    Поле для работы с ContentType в сериализаторах.

    Преобразует строковое представление (app_label.model) в объект ContentType
    и обратно для использования в API.
    """

    def to_representation(self, value):
        """
        Преобразование объекта ContentType в строковое представление.

        Args:
            value: Объект ContentType для сериализации.

        Returns:
            str: Строковое представление типа контента в формате app_label.model.
        """
        if not value:
            return None

        if isinstance(value, ContentType):
            return f"{value.app_label}.{value.model}"

        return value

    def to_internal_value(self, data):
        """
        Преобразование строкового представления в объект ContentType.

        Args:
            data: Строковое представление типа контента в формате app_label.model.

        Returns:
            ContentType: Объект ContentType, соответствующий переданной строке.

        Raises:
            serializers.ValidationError: Если тип контента не найден или формат неверен.
        """
        if not data:
            return None

        try:
            app_label, model = data.split('.')
            return ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                "Неверный формат типа контента. Должен быть в формате 'app_label.model'."
            )


class GenericRelatedField(serializers.Field):
    """
    Поле для работы с GenericForeignKey в сериализаторах.

    Позволяет сериализовать и десериализовать объекты, связанные через
    ContentType, используя соответствующие сериализаторы.
    """

    def __init__(self, serializer_mapping=None, **kwargs):
        """
        Инициализирует поле с маппингом типов контента к сериализаторам.

        Args:
            serializer_mapping: Словарь сопоставления ContentType к сериализаторам.
            **kwargs: Дополнительные аргументы для базового класса.
        """
        super().__init__(**kwargs)
        self.serializer_mapping = serializer_mapping or {}

    def to_representation(self, value):
        """
        Преобразование объекта в представление с использованием соответствующего сериализатора.

        Args:
            value: Объект для сериализации.

        Returns:
            dict: Сериализованное представление объекта.
        """
        if not value:
            return None

        content_type = ContentType.objects.get_for_model(value)
        key = f"{content_type.app_label}.{content_type.model}"

        if key in self.serializer_mapping:
            serializer = self.serializer_mapping[key]
            return serializer(value, context=self.context).data

        # Базовое представление, если соответствующий сериализатор не найден
        return {
            'id': value.pk,
            'type': key,
            'str': str(value)
        }

    def to_internal_value(self, data):
        """
        Преобразование данных в объект с использованием типа контента и ID.

        Args:
            data: Данные для десериализации, содержащие тип контента и ID объекта.

        Returns:
            object: Объект, соответствующий переданным данным.

        Raises:
            serializers.ValidationError: Если объект не найден или данные некорректны.
        """
        if not isinstance(data, dict) or 'type' not in data or 'id' not in data:
            raise serializers.ValidationError(
                "Данные должны содержать 'type' (в формате 'app_label.model') и 'id'."
            )

        try:
            content_type = ContentTypeField().to_internal_value(data['type'])
            model_class = content_type.model_class()
            return model_class.objects.get(pk=data['id'])
        except (ContentType.DoesNotExist, ObjectDoesNotExist, ValueError):
            raise serializers.ValidationError("Объект не найден.")


class DynamicFieldsModelSerializer(BaseModelSerializer):
    """
    Сериализатор с динамическим набором полей.

    Позволяет указать список полей для включения или исключения при сериализации,
    что упрощает создание разных представлений одной модели для разных задач.
    """

    def __init__(self, *args, **kwargs):
        """
        Инициализирует сериализатор с возможностью указания полей.

        Args:
            fields: Список полей для включения.
            exclude: Список полей для исключения.
            *args: Аргументы для базового класса.
            **kwargs: Именованные аргументы для базового класса.
        """
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            # Исключаем все поля, которых нет в списке fields
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            # Исключаем указанные поля
            for field_name in exclude:
                if field_name in self.fields:
                    self.fields.pop(field_name)


class ErrorSerializer(serializers.Serializer):
    """
    Сериализатор для стандартизации ответов с ошибками.

    Обеспечивает единый формат ответов с ошибками по всему API.
    """

    error = serializers.CharField()
    details = serializers.JSONField(required=False)


class PaginatedResponseSerializer(serializers.Serializer):
    """
    Сериализатор для стандартизации пагинированных ответов.

    Предоставляет структуру для отображения данных с пагинацией.
    """

    count = serializers.IntegerField(help_text="Общее количество объектов")
    next = serializers.URLField(allow_null=True, help_text="URL следующей страницы")
    previous = serializers.URLField(allow_null=True, help_text="URL предыдущей страницы")
    results = serializers.ListField(child=serializers.DictField(), help_text="Список объектов на странице")
"""
Сериализаторы для работы с тегами.

Этот модуль предоставляет сериализаторы для API тегов,
позволяющие работать с тегами и связями объектов с тегами.
"""

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from core.api.serializers.base import (
    BaseModelSerializer,
    ContentTypeField,
    DynamicFieldsModelSerializer
)
from core.models.tags import Tag, TaggedItem as GenericTaggedItem


class TagSerializer(BaseModelSerializer):
    """
    Сериализатор для модели тегов.

    Обеспечивает преобразование модели тегов в JSON и обратно.
    """

    class Meta:
        """
        Метаданные сериализатора тегов.
        """
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class TagCreateSerializer(BaseModelSerializer):
    """
    Сериализатор для создания тегов.

    Обеспечивает валидацию данных при создании новых тегов.
    """

    class Meta:
        """
        Метаданные сериализатора создания тегов.
        """
        model = Tag
        fields = ['name', 'description', 'color']

    def validate_name(self, value):
        """
        Проверяет уникальность имени тега.

        Args:
            value: Значение имени для проверки.

        Returns:
            str: Проверенное значение имени.

        Raises:
            serializers.ValidationError: Если имя не уникально.
        """
        if Tag.objects.filter(name=value).exists():
            raise serializers.ValidationError("Тег с таким именем уже существует.")
        return value


class TagUpdateSerializer(BaseModelSerializer):
    """
    Сериализатор для обновления тегов.

    Обеспечивает валидацию данных при обновлении существующих тегов.
    """

    class Meta:
        """
        Метаданные сериализатора обновления тегов.
        """
        model = Tag
        fields = ['name', 'description', 'color']

    def validate_name(self, value):
        """
        Проверяет уникальность имени тега при обновлении.

        Args:
            value: Значение имени для проверки.

        Returns:
            str: Проверенное значение имени.

        Raises:
            serializers.ValidationError: Если имя не уникально.
        """
        instance = self.instance
        if Tag.objects.filter(name=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Тег с таким именем уже существует.")
        return value


class GenericTaggedItemSerializer(BaseModelSerializer):
    """
    Сериализатор для связей между объектами и тегами.

    Обеспечивает преобразование модели связей в JSON и обратно.
    """

    content_type = ContentTypeField()
    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    tag_details = TagSerializer(source='tag', read_only=True)

    class Meta:
        """
        Метаданные сериализатора связей.
        """
        model = GenericTaggedItem
        fields = ['id', 'tag', 'tag_details', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaggedItemCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания связей между объектами и тегами.

    Обеспечивает валидацию данных при создании новых связей.
    """

    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    content_type = ContentTypeField()
    object_id = serializers.CharField()

    def validate(self, data):
        """
        Проверяет валидность данных для создания связи.

        Args:
            data: Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны или связь уже существует.
        """
        # Проверяем существование объекта
        content_type = data['content_type']
        object_id = data['object_id']

        try:
            model_class = content_type.model_class()
            obj = model_class.objects.get(pk=object_id)
        except Exception:
            raise serializers.ValidationError("Объект не найден.")

        # Проверяем, не существует ли уже такая связь
        if GenericTaggedItem.objects.filter(
                content_type=content_type,
                object_id=object_id,
                tag=data['tag']
        ).exists():
            raise serializers.ValidationError("Этот тег уже присвоен данному объекту.")

        return data

    def create(self, validated_data):
        """
        Создает связь между объектом и тегом.

        Args:
            validated_data: Валидированные данные для создания связи.

        Returns:
            GenericTaggedItem: Созданная связь.
        """
        return GenericTaggedItem.objects.create(**validated_data)


class TaggedItemDeleteSerializer(serializers.Serializer):
    """
    Сериализатор для удаления связей между объектами и тегами.

    Обеспечивает валидацию данных при удалении связей.
    """

    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    content_type = ContentTypeField()
    object_id = serializers.CharField()

    def validate(self, data):
        """
        Проверяет валидность данных для удаления связи.

        Args:
            data: Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если связь не найдена.
        """
        content_type = data['content_type']
        object_id = data['object_id']
        tag = data['tag']

        try:
            tagged_item = GenericTaggedItem.objects.get(
                content_type=content_type,
                object_id=object_id,
                tag=tag
            )
            data['tagged_item'] = tagged_item
        except GenericTaggedItem.DoesNotExist:
            raise serializers.ValidationError("Тег не присвоен данному объекту.")

        return data


class TagWithObjectCountSerializer(TagSerializer):
    """
    Сериализатор для тегов с количеством связанных объектов.

    Расширяет базовый сериализатор тегов, добавляя количество связанных объектов.
    """

    objects_count = serializers.IntegerField(read_only=True)

    class Meta(TagSerializer.Meta):
        """
        Метаданные сериализатора тегов с количеством объектов.
        """
        fields = TagSerializer.Meta.fields + ['objects_count']


class ObjectTagsSerializer(serializers.Serializer):
    """
    Сериализатор для получения тегов, связанных с объектом.

    Предоставляет информацию о всех тегах, присвоенных конкретному объекту.
    """

    content_type = ContentTypeField()
    object_id = serializers.CharField()
    tags = TagSerializer(many=True, read_only=True)


class BulkTagsSerializer(serializers.Serializer):
    """
    Сериализатор для массового присвоения тегов объекту.

    Позволяет за один запрос присвоить несколько тегов объекту.
    """

    content_type = ContentTypeField()
    object_id = serializers.CharField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    def validate(self, data):
        """
        Проверяет валидность данных для массового присвоения тегов.

        Args:
            data: Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если объект не найден.
        """
        # Проверяем существование объекта
        content_type = data['content_type']
        object_id = data['object_id']

        try:
            model_class = content_type.model_class()
            obj = model_class.objects.get(pk=object_id)
        except Exception:
            raise serializers.ValidationError("Объект не найден.")

        return data
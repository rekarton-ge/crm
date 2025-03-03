"""
Сериализаторы для работы с категориями.

Этот модуль предоставляет сериализаторы для API категорий,
позволяющие просматривать и изменять категории.
"""

from rest_framework import serializers

from core.api.serializers.base import BaseModelSerializer
from core.models.metadata import Category


class CategorySerializer(BaseModelSerializer):
    """
    Сериализатор для модели категорий.

    Обеспечивает преобразование модели категорий в JSON и обратно,
    для работы с API категорий.
    """
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        """
        Метаданные сериализатора категорий.
        """
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'parent_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_parent_name(self, obj):
        """
        Получает имя родительской категории.
        
        Args:
            obj: Объект категории
            
        Returns:
            str: Имя родительской категории или None, если родительской категории нет
        """
        return obj.parent.name if obj.parent else None


class CategoryCreateSerializer(BaseModelSerializer):
    """
    Сериализатор для создания категорий.

    Обеспечивает валидацию данных при создании новых категорий
    через API.
    """

    class Meta:
        """
        Метаданные сериализатора создания категорий.
        """
        model = Category
        fields = ['name', 'slug', 'description', 'parent']

    def validate_slug(self, value):
        """
        Проверяет уникальность slug категории.

        Args:
            value: Значение slug для проверки.

        Returns:
            str: Проверенное значение slug.

        Raises:
            serializers.ValidationError: Если slug не уникален.
        """
        if Category.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Категория с таким slug уже существует.")
        return value


class CategoryUpdateSerializer(BaseModelSerializer):
    """
    Сериализатор для обновления категорий.

    Обеспечивает валидацию данных при обновлении существующих категорий
    через API.
    """

    class Meta:
        """
        Метаданные сериализатора обновления категорий.
        """
        model = Category
        fields = ['name', 'description', 'parent']
        
    def validate_parent(self, value):
        """
        Проверяет, что родительская категория не является текущей категорией
        или её потомком.

        Args:
            value: Значение родительской категории для проверки.

        Returns:
            Category: Проверенное значение родительской категории.

        Raises:
            serializers.ValidationError: Если родительская категория является текущей категорией
                                        или её потомком.
        """
        if not value:
            return value
            
        instance = self.instance
        
        # Проверяем, что родительская категория не является текущей категорией
        if value.id == instance.id:
            raise serializers.ValidationError("Категория не может быть родительской для самой себя.")
            
        # Проверяем, что родительская категория не является потомком текущей категории
        descendants = []
        queue = list(Category.objects.filter(parent=instance))
        
        while queue:
            child = queue.pop(0)
            descendants.append(child.id)
            queue.extend(Category.objects.filter(parent=child))
            
        if value.id in descendants:
            raise serializers.ValidationError("Родительская категория не может быть потомком текущей категории.")
            
        return value 
"""
Сервис для работы с тегами.

Этот модуль предоставляет сервис для работы с тегами и категориями.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple, Type

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType

from core.models import Tag, TaggedItem, Category

User = get_user_model()
logger = logging.getLogger(__name__)


class TagFilter:
    """
    Класс для фильтрации тегов.
    """
    
    def __init__(self, name: Optional[str] = None, slug: Optional[str] = None,
                 color: Optional[str] = None, created_by: Optional[User] = None,
                 category: Optional[Category] = None):
        """
        Инициализирует фильтр тегов.
        
        Args:
            name: Имя тега
            slug: Slug тега
            color: Цвет тега
            created_by: Пользователь, создавший тег
            category: Категория тега
        """
        self.name = name
        self.slug = slug
        self.color = color
        self.created_by = created_by
        self.category = category
    
    def get_queryset(self) -> models.QuerySet:
        """
        Возвращает отфильтрованный QuerySet.
        
        Returns:
            models.QuerySet: Отфильтрованный QuerySet
        """
        queryset = Tag.objects.all()
        
        if self.name:
            queryset = queryset.filter(name__icontains=self.name)
        
        if self.slug:
            queryset = queryset.filter(slug=self.slug)
        
        if self.color:
            queryset = queryset.filter(color=self.color)
        
        if self.created_by:
            queryset = queryset.filter(created_by=self.created_by)
        
        if self.category:
            queryset = queryset.filter(category=self.category)
        
        return queryset.order_by('name')


class TagManager:
    """
    Менеджер тегов.
    """
    
    def __init__(self, user: Optional[User] = None):
        """
        Инициализирует менеджер тегов.
        
        Args:
            user: Пользователь
        """
        self.user = user
    
    def create_tag(self, name: str, color: Optional[str] = None,
                  description: Optional[str] = None, category: Optional[Category] = None,
                  slug: Optional[str] = None) -> Tag:
        """
        Создает тег.
        
        Args:
            name: Имя тега
            color: Цвет тега
            description: Описание тега
            category: Категория тега
            slug: Slug тега
            
        Returns:
            Tag: Созданный тег
        """
        if not slug:
            slug = slugify(name)
        
        # Проверяем, существует ли тег с таким slug
        if Tag.objects.filter(slug=slug).exists():
            # Добавляем числовой суффикс к slug
            i = 1
            while Tag.objects.filter(slug=f"{slug}-{i}").exists():
                i += 1
            slug = f"{slug}-{i}"
        
        tag = Tag.objects.create(
            name=name,
            slug=slug,
            color=color,
            description=description,
            category=category,
            created_by=self.user,
        )
        
        logger.info(f"Tag created: {tag.name} (by {self.user.username if self.user else 'anonymous'})")
        
        return tag
    
    def update_tag(self, tag: Tag, name: Optional[str] = None, color: Optional[str] = None,
                  description: Optional[str] = None, category: Optional[Category] = None,
                  slug: Optional[str] = None) -> Tag:
        """
        Обновляет тег.
        
        Args:
            tag: Тег для обновления
            name: Новое имя тега
            color: Новый цвет тега
            description: Новое описание тега
            category: Новая категория тега
            slug: Новый slug тега
            
        Returns:
            Tag: Обновленный тег
        """
        if name is not None:
            tag.name = name
        
        if color is not None:
            tag.color = color
        
        if description is not None:
            tag.description = description
        
        if category is not None:
            tag.category = category
        
        if slug is not None:
            # Проверяем, существует ли другой тег с таким slug
            if Tag.objects.filter(slug=slug).exclude(pk=tag.pk).exists():
                # Добавляем числовой суффикс к slug
                i = 1
                while Tag.objects.filter(slug=f"{slug}-{i}").exclude(pk=tag.pk).exists():
                    i += 1
                slug = f"{slug}-{i}"
            
            tag.slug = slug
        
        tag.save()
        
        logger.info(f"Tag updated: {tag.name} (by {self.user.username if self.user else 'anonymous'})")
        
        return tag
    
    def delete_tag(self, tag: Tag) -> None:
        """
        Удаляет тег.
        
        Args:
            tag: Тег для удаления
        """
        tag_name = tag.name
        tag.delete()
        
        logger.info(f"Tag deleted: {tag_name} (by {self.user.username if self.user else 'anonymous'})")
    
    def get_tags(self, filter_params: Optional[TagFilter] = None) -> List[Tag]:
        """
        Получает теги.
        
        Args:
            filter_params: Параметры фильтрации
            
        Returns:
            List[Tag]: Список тегов
        """
        queryset = Tag.objects.all().order_by('name')
        
        if filter_params:
            queryset = filter_params.get_queryset()
        
        return list(queryset)
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """
        Получает тег по ID.
        
        Args:
            tag_id: ID тега
            
        Returns:
            Optional[Tag]: Тег или None, если тег не найден
        """
        try:
            return Tag.objects.get(pk=tag_id)
        except Tag.DoesNotExist:
            return None
    
    def get_tag_by_slug(self, slug: str) -> Optional[Tag]:
        """
        Получает тег по slug.
        
        Args:
            slug: Slug тега
            
        Returns:
            Optional[Tag]: Тег или None, если тег не найден
        """
        try:
            return Tag.objects.get(slug=slug)
        except Tag.DoesNotExist:
            return None
    
    def search_tags(self, query: str) -> List[Tag]:
        """
        Ищет теги по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            List[Tag]: Список тегов
        """
        queryset = Tag.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query) |
            Q(description__icontains=query)
        ).order_by('name')
        
        return list(queryset)
    
    def get_popular_tags(self, limit: int = 10) -> List[Tuple[Tag, int]]:
        """
        Получает популярные теги.
        
        Args:
            limit: Максимальное количество тегов
            
        Returns:
            List[Tuple[Tag, int]]: Список тегов с количеством использований
        """
        queryset = Tag.objects.annotate(
            usage_count=Count('tagged_items')
        ).order_by('-usage_count')[:limit]
        
        return [(tag, tag.usage_count) for tag in queryset]
    
    def tag_object(self, obj: models.Model, tags: List[Union[Tag, str]]) -> List[TaggedItem]:
        """
        Добавляет теги к объекту.
        
        Args:
            obj: Объект для тегирования
            tags: Список тегов или имен тегов
            
        Returns:
            List[TaggedItem]: Список созданных связей
        """
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        
        # Удаляем существующие теги
        TaggedItem.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).delete()
        
        tagged_items = []
        
        for tag in tags:
            if isinstance(tag, str):
                # Если тег передан как строка, ищем его по имени или создаем новый
                try:
                    tag_obj = Tag.objects.get(name=tag)
                except Tag.DoesNotExist:
                    tag_obj = self.create_tag(name=tag)
            else:
                tag_obj = tag
            
            tagged_item = TaggedItem.objects.create(
                tag=tag_obj,
                content_type=content_type,
                object_id=object_id,
                created_by=self.user,
            )
            
            tagged_items.append(tagged_item)
        
        logger.info(
            f"Object tagged: {obj} with tags {', '.join(str(tag) for tag in tags)} "
            f"(by {self.user.username if self.user else 'anonymous'})"
        )
        
        return tagged_items
    
    def get_objects_with_tag(self, tag: Union[Tag, str], model: Optional[Type[models.Model]] = None) -> List[models.Model]:
        """
        Получает объекты с указанным тегом.
        
        Args:
            tag: Тег или имя тега
            model: Модель объектов (если None, возвращаются объекты всех моделей)
            
        Returns:
            List[models.Model]: Список объектов с указанным тегом
        """
        if isinstance(tag, str):
            try:
                tag = Tag.objects.get(name=tag)
            except Tag.DoesNotExist:
                return []
        
        queryset = TaggedItem.objects.filter(tag=tag)
        
        if model:
            content_type = ContentType.objects.get_for_model(model)
            queryset = queryset.filter(content_type=content_type)
        
        objects = []
        
        for tagged_item in queryset:
            try:
                obj = tagged_item.content_type.get_object_for_this_type(pk=tagged_item.object_id)
                objects.append(obj)
            except models.ObjectDoesNotExist:
                # Объект был удален, но связь осталась
                tagged_item.delete()
        
        return objects
    
    def get_tags_for_object(self, obj: models.Model) -> List[Tag]:
        """
        Получает теги для объекта.
        
        Args:
            obj: Объект
            
        Returns:
            List[Tag]: Список тегов
        """
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        
        queryset = TaggedItem.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).select_related('tag')
        
        return [tagged_item.tag for tagged_item in queryset]
    
    def remove_tag_from_object(self, obj: models.Model, tag: Union[Tag, str]) -> None:
        """
        Удаляет тег с объекта.
        
        Args:
            obj: Объект
            tag: Тег или имя тега
        """
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        
        if isinstance(tag, str):
            try:
                tag = Tag.objects.get(name=tag)
            except Tag.DoesNotExist:
                return
        
        TaggedItem.objects.filter(
            content_type=content_type,
            object_id=object_id,
            tag=tag
        ).delete()
        
        logger.info(
            f"Tag removed from object: {tag} from {obj} "
            f"(by {self.user.username if self.user else 'anonymous'})"
        )


class TagService:
    """
    Сервис для работы с тегами.
    """
    
    def __init__(self, user: Optional[User] = None):
        """
        Инициализирует сервис тегов.
        
        Args:
            user: Пользователь
        """
        self.user = user
        self.tag_manager = TagManager(user)
    
    def create_tag(self, name: str, color: Optional[str] = None,
                  description: Optional[str] = None, category: Optional[Category] = None,
                  slug: Optional[str] = None) -> Tag:
        """
        Создает тег.
        
        Args:
            name: Имя тега
            color: Цвет тега
            description: Описание тега
            category: Категория тега
            slug: Slug тега
            
        Returns:
            Tag: Созданный тег
        """
        return self.tag_manager.create_tag(name, color, description, category, slug)
    
    def update_tag(self, tag: Tag, name: Optional[str] = None, color: Optional[str] = None,
                  description: Optional[str] = None, category: Optional[Category] = None,
                  slug: Optional[str] = None) -> Tag:
        """
        Обновляет тег.
        
        Args:
            tag: Тег для обновления
            name: Новое имя тега
            color: Новый цвет тега
            description: Новое описание тега
            category: Новая категория тега
            slug: Новый slug тега
            
        Returns:
            Tag: Обновленный тег
        """
        return self.tag_manager.update_tag(tag, name, color, description, category, slug)
    
    def delete_tag(self, tag: Tag) -> None:
        """
        Удаляет тег.
        
        Args:
            tag: Тег для удаления
        """
        self.tag_manager.delete_tag(tag)
    
    def get_tags(self, filter_params: Optional[TagFilter] = None) -> List[Tag]:
        """
        Получает теги.
        
        Args:
            filter_params: Параметры фильтрации
            
        Returns:
            List[Tag]: Список тегов
        """
        return self.tag_manager.get_tags(filter_params)
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """
        Получает тег по ID.
        
        Args:
            tag_id: ID тега
            
        Returns:
            Optional[Tag]: Тег или None, если тег не найден
        """
        return self.tag_manager.get_tag(tag_id)
    
    def get_tag_by_slug(self, slug: str) -> Optional[Tag]:
        """
        Получает тег по slug.
        
        Args:
            slug: Slug тега
            
        Returns:
            Optional[Tag]: Тег или None, если тег не найден
        """
        return self.tag_manager.get_tag_by_slug(slug)
    
    def search_tags(self, query: str) -> List[Tag]:
        """
        Ищет теги по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            List[Tag]: Список тегов
        """
        return self.tag_manager.search_tags(query)
    
    def get_popular_tags(self, limit: int = 10) -> List[Tuple[Tag, int]]:
        """
        Получает популярные теги.
        
        Args:
            limit: Максимальное количество тегов
            
        Returns:
            List[Tuple[Tag, int]]: Список тегов с количеством использований
        """
        return self.tag_manager.get_popular_tags(limit)
    
    def tag_object(self, obj: models.Model, tags: List[Union[Tag, str]]) -> List[TaggedItem]:
        """
        Добавляет теги к объекту.
        
        Args:
            obj: Объект для тегирования
            tags: Список тегов или имен тегов
            
        Returns:
            List[TaggedItem]: Список созданных связей
        """
        return self.tag_manager.tag_object(obj, tags)
    
    def get_objects_with_tag(self, tag: Union[Tag, str], model: Optional[Type[models.Model]] = None) -> List[models.Model]:
        """
        Получает объекты с указанным тегом.
        
        Args:
            tag: Тег или имя тега
            model: Модель объектов (если None, возвращаются объекты всех моделей)
            
        Returns:
            List[models.Model]: Список объектов с указанным тегом
        """
        return self.tag_manager.get_objects_with_tag(tag, model)
    
    def get_tags_for_object(self, obj: models.Model) -> List[Tag]:
        """
        Получает теги для объекта.
        
        Args:
            obj: Объект
            
        Returns:
            List[Tag]: Список тегов
        """
        return self.tag_manager.get_tags_for_object(obj)
    
    def remove_tag_from_object(self, obj: models.Model, tag: Union[Tag, str]) -> None:
        """
        Удаляет тег с объекта.
        
        Args:
            obj: Объект
            tag: Тег или имя тега
        """
        self.tag_manager.remove_tag_from_object(obj, tag)
    
    @transaction.atomic
    def merge_tags(self, source_tags: List[Tag], target_tag: Tag) -> None:
        """
        Объединяет теги.
        
        Args:
            source_tags: Исходные теги
            target_tag: Целевой тег
        """
        for source_tag in source_tags:
            # Перемещаем все связи с исходного тега на целевой
            TaggedItem.objects.filter(tag=source_tag).update(tag=target_tag)
            
            # Удаляем исходный тег
            source_tag.delete()
        
        logger.info(
            f"Tags merged: {', '.join(str(tag) for tag in source_tags)} into {target_tag} "
            f"(by {self.user.username if self.user else 'anonymous'})"
        )
    
    def create_category(self, name: str, description: Optional[str] = None,
                       parent: Optional[Category] = None, slug: Optional[str] = None) -> Category:
        """
        Создает категорию.
        
        Args:
            name: Имя категории
            description: Описание категории
            parent: Родительская категория
            slug: Slug категории
            
        Returns:
            Category: Созданная категория
        """
        if not slug:
            slug = slugify(name)
        
        # Проверяем, существует ли категория с таким slug
        if Category.objects.filter(slug=slug).exists():
            # Добавляем числовой суффикс к slug
            i = 1
            while Category.objects.filter(slug=f"{slug}-{i}").exists():
                i += 1
            slug = f"{slug}-{i}"
        
        category = Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            parent=parent,
            created_by=self.user,
        )
        
        logger.info(f"Category created: {category.name} (by {self.user.username if self.user else 'anonymous'})")
        
        return category
    
    def update_category(self, category: Category, name: Optional[str] = None,
                       description: Optional[str] = None, parent: Optional[Category] = None,
                       slug: Optional[str] = None) -> Category:
        """
        Обновляет категорию.
        
        Args:
            category: Категория для обновления
            name: Новое имя категории
            description: Новое описание категории
            parent: Новая родительская категория
            slug: Новый slug категории
            
        Returns:
            Category: Обновленная категория
        """
        if name is not None:
            category.name = name
        
        if description is not None:
            category.description = description
        
        if parent is not None:
            # Проверяем, не является ли родительская категория потомком текущей
            if parent.pk == category.pk or (parent.parent and parent.parent.pk == category.pk):
                raise ValueError("Cannot set a category as its own parent or child")
            
            category.parent = parent
        
        if slug is not None:
            # Проверяем, существует ли другая категория с таким slug
            if Category.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                # Добавляем числовой суффикс к slug
                i = 1
                while Category.objects.filter(slug=f"{slug}-{i}").exclude(pk=category.pk).exists():
                    i += 1
                slug = f"{slug}-{i}"
            
            category.slug = slug
        
        category.save()
        
        logger.info(f"Category updated: {category.name} (by {self.user.username if self.user else 'anonymous'})")
        
        return category
    
    def delete_category(self, category: Category) -> None:
        """
        Удаляет категорию.
        
        Args:
            category: Категория для удаления
        """
        category_name = category.name
        category.delete()
        
        logger.info(f"Category deleted: {category_name} (by {self.user.username if self.user else 'anonymous'})")
    
    def get_categories(self) -> List[Category]:
        """
        Получает категории.
        
        Returns:
            List[Category]: Список категорий
        """
        return list(Category.objects.all().order_by('name'))
    
    def get_category(self, category_id: int) -> Optional[Category]:
        """
        Получает категорию по ID.
        
        Args:
            category_id: ID категории
            
        Returns:
            Optional[Category]: Категория или None, если категория не найдена
        """
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return None
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """
        Получает категорию по slug.
        
        Args:
            slug: Slug категории
            
        Returns:
            Optional[Category]: Категория или None, если категория не найдена
        """
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """
        Получает дерево категорий.
        
        Returns:
            List[Dict[str, Any]]: Дерево категорий
        """
        def build_tree(parent: Optional[Category] = None) -> List[Dict[str, Any]]:
            """
            Рекурсивно строит дерево категорий.
            
            Args:
                parent: Родительская категория
                
            Returns:
                List[Dict[str, Any]]: Дерево категорий
            """
            if parent:
                categories = Category.objects.filter(parent=parent).order_by('name')
            else:
                categories = Category.objects.filter(parent__isnull=True).order_by('name')
            
            result = []
            
            for category in categories:
                children = build_tree(category)
                
                result.append({
                    'id': category.pk,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'children': children,
                })
            
            return result
        
        return build_tree()
    
    def get_tags_by_category(self, category: Category) -> List[Tag]:
        """
        Получает теги по категории.
        
        Args:
            category: Категория
            
        Returns:
            List[Tag]: Список тегов
        """
        return list(Tag.objects.filter(category=category).order_by('name'))

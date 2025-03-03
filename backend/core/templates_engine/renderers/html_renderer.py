"""
Рендерер HTML-шаблонов.

Этот модуль содержит рендерер для HTML-шаблонов.
"""

import os
from typing import Any, Dict, Optional

from django.template import Context, Template
from django.template.loader import get_template

from core.templates_engine.renderers.base import BaseTemplateRenderer


class HTMLTemplateRenderer(BaseTemplateRenderer):
    """
    Рендерер HTML-шаблонов.
    
    Рендерит HTML-шаблоны с использованием Django Template Engine.
    """
    
    def __init__(self, template_dirs: Optional[list] = None):
        """
        Инициализация рендерера HTML-шаблонов.
        
        Args:
            template_dirs (list, optional): Список директорий с шаблонами.
        """
        self.template_dirs = template_dirs or []
    
    def render(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Рендерит HTML-шаблон с использованием контекста.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренный HTML-шаблон.
        """
        # Создаем шаблон Django
        template = Template(template_content)
        
        # Создаем контекст Django
        django_context = Context(context)
        
        # Рендерим шаблон
        return template.render(django_context)
    
    def render_to_file(self, template_content: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит HTML-шаблон с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Рендерим шаблон
        rendered_content = self.render(template_content, context)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
    
    def render_from_file(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Рендерит HTML-шаблон из файла с использованием контекста.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренный HTML-шаблон.
        """
        # Загружаем шаблон
        template = get_template(template_path)
        
        # Рендерим шаблон
        return template.render(context)
    
    def render_from_file_to_file(self, template_path: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит HTML-шаблон из файла с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Рендерим шаблон
        rendered_content = self.render_from_file(template_path, context)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)

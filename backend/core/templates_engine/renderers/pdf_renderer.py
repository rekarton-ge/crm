"""
Рендерер PDF-шаблонов.

Этот модуль содержит рендерер для PDF-шаблонов.
"""

import os
from typing import Any, Dict, Optional

from django.template import Context, Template
from weasyprint import HTML

from core.templates_engine.renderers import BaseTemplateRenderer
from core.templates_engine.renderers.html_renderer import HTMLTemplateRenderer


class PDFTemplateRenderer(BaseTemplateRenderer):
    """
    Рендерер PDF-шаблонов.
    
    Рендерит PDF-шаблоны с использованием WeasyPrint.
    """
    
    def __init__(self, template_dirs: Optional[list] = None, html_renderer: Optional[HTMLTemplateRenderer] = None):
        """
        Инициализация рендерера PDF-шаблонов.
        
        Args:
            template_dirs (list, optional): Список директорий с шаблонами.
            html_renderer (HTMLTemplateRenderer, optional): Рендерер HTML-шаблонов.
        """
        self.template_dirs = template_dirs or []
        self.html_renderer = html_renderer or HTMLTemplateRenderer(template_dirs)
    
    def render(self, template_content: str, context: Dict[str, Any]) -> bytes:
        """
        Рендерит PDF-шаблон с использованием контекста.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            bytes: Отрендеренный PDF-шаблон.
        """
        # Рендерим HTML-шаблон
        html_content = self.html_renderer.render(template_content, context)
        
        # Создаем PDF из HTML
        pdf = HTML(string=html_content).write_pdf()
        
        return pdf
    
    def render_to_file(self, template_content: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит PDF-шаблон с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Рендерим PDF-шаблон
        pdf_content = self.render(template_content, context)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
    
    def render_from_file(self, template_path: str, context: Dict[str, Any]) -> bytes:
        """
        Рендерит PDF-шаблон из файла с использованием контекста.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            bytes: Отрендеренный PDF-шаблон.
        """
        # Рендерим HTML-шаблон из файла
        html_content = self.html_renderer.render_from_file(template_path, context)
        
        # Создаем PDF из HTML
        pdf = HTML(string=html_content).write_pdf()
        
        return pdf
    
    def render_from_file_to_file(self, template_path: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит PDF-шаблон из файла с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Рендерим PDF-шаблон из файла
        pdf_content = self.render_from_file(template_path, context)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
    
    def render_from_html(self, html_content: str) -> bytes:
        """
        Рендерит PDF из HTML-содержимого.
        
        Args:
            html_content (str): HTML-содержимое.
        
        Returns:
            bytes: Отрендеренный PDF.
        """
        # Создаем PDF из HTML
        pdf = HTML(string=html_content).write_pdf()
        
        return pdf
    
    def render_from_html_to_file(self, html_content: str, output_path: str) -> None:
        """
        Рендерит PDF из HTML-содержимого и сохраняет результат в файл.
        
        Args:
            html_content (str): HTML-содержимое.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Рендерим PDF из HTML
        pdf_content = self.render_from_html(html_content)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        with open(output_path, 'wb') as f:
            f.write(pdf_content)

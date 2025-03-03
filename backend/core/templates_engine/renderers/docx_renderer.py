"""
Рендерер DOCX-шаблонов.

Этот модуль содержит рендерер для DOCX-шаблонов.
"""

import os
from typing import Any, Dict, Optional

from docxtpl import DocxTemplate

from core.templates_engine.renderers import BaseTemplateRenderer


class DocxTemplateRenderer(BaseTemplateRenderer):
    """
    Рендерер DOCX-шаблонов.
    
    Рендерит DOCX-шаблоны с использованием python-docx-template.
    """
    
    def __init__(self, template_dirs: Optional[list] = None):
        """
        Инициализация рендерера DOCX-шаблонов.
        
        Args:
            template_dirs (list, optional): Список директорий с шаблонами.
        """
        self.template_dirs = template_dirs or []
    
    def render(self, template_content: str, context: Dict[str, Any]) -> bytes:
        """
        Рендерит DOCX-шаблон с использованием контекста.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            bytes: Отрендеренный DOCX-шаблон.
        
        Raises:
            ValueError: Если template_content не является путем к файлу DOCX.
        """
        # python-docx-template не поддерживает рендеринг из строки,
        # поэтому template_content должен быть путем к файлу DOCX
        raise ValueError(
            "Рендеринг DOCX-шаблона из строки не поддерживается. "
            "Используйте render_from_file или render_from_file_to_file."
        )
    
    def render_to_file(self, template_content: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит DOCX-шаблон с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        
        Raises:
            ValueError: Если template_content не является путем к файлу DOCX.
        """
        # python-docx-template не поддерживает рендеринг из строки,
        # поэтому template_content должен быть путем к файлу DOCX
        raise ValueError(
            "Рендеринг DOCX-шаблона из строки не поддерживается. "
            "Используйте render_from_file или render_from_file_to_file."
        )
    
    def render_from_file(self, template_path: str, context: Dict[str, Any]) -> bytes:
        """
        Рендерит DOCX-шаблон из файла с использованием контекста.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            bytes: Отрендеренный DOCX-шаблон.
        """
        # Создаем временный файл для сохранения результата
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Рендерим DOCX-шаблон из файла в временный файл
            self.render_from_file_to_file(template_path, context, temp_path)
            
            # Читаем содержимое временного файла
            with open(temp_path, 'rb') as f:
                return f.read()
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def render_from_file_to_file(self, template_path: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит DOCX-шаблон из файла с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_path (str): Путь к файлу шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        # Загружаем шаблон
        doc = DocxTemplate(template_path)
        
        # Рендерим шаблон
        doc.render(context)
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем результат в файл
        doc.save(output_path)
    
    def get_template_variables(self, template_path: str) -> list:
        """
        Возвращает список переменных, используемых в шаблоне.
        
        Args:
            template_path (str): Путь к файлу шаблона.
        
        Returns:
            list: Список переменных.
        """
        # Загружаем шаблон
        doc = DocxTemplate(template_path)
        
        # Получаем список переменных
        return doc.get_undeclared_template_variables()

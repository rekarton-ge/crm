"""
Базовый класс для рендереров шаблонов.

Этот модуль содержит базовый класс для рендереров шаблонов.
"""

from typing import Dict, Any


class BaseTemplateRenderer:
    """
    Базовый класс для рендереров шаблонов.
    
    Определяет интерфейс для рендереров шаблонов.
    """
    
    def render(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Рендерит шаблон с использованием контекста.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            str: Отрендеренный шаблон.
        """
        raise NotImplementedError("Метод render должен быть переопределен в подклассе")
    
    def render_to_file(self, template_content: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Рендерит шаблон с использованием контекста и сохраняет результат в файл.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
            output_path (str): Путь к файлу для сохранения результата.
        """
        raise NotImplementedError("Метод render_to_file должен быть переопределен в подклассе") 
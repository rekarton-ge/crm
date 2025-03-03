"""
Парсеры шаблонов.

Этот модуль содержит парсеры для шаблонов.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from core.templates_engine.variables import TemplateVariable, VariableRegistry


class VariableParser:
    """
    Парсер переменных шаблона.
    
    Извлекает переменные из шаблона и проверяет их.
    """
    
    def __init__(self, registry: Optional[VariableRegistry] = None):
        """
        Инициализация парсера переменных.
        
        Args:
            registry (VariableRegistry, optional): Реестр переменных.
        """
        self.registry = registry or VariableRegistry()
    
    def parse(self, template_content: str) -> Set[str]:
        """
        Извлекает имена переменных из шаблона.
        
        Args:
            template_content (str): Содержимое шаблона.
        
        Returns:
            Set[str]: Множество имен переменных.
        """
        return self.registry.extract_variables_from_template(template_content)
    
    def validate(self, template_content: str, context: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Проверяет контекст шаблона.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            Tuple[bool, Dict[str, str]]: Флаг валидности и словарь с ошибками.
        """
        # Извлекаем имена переменных из шаблона
        template_variables = self.parse(template_content)
        
        # Проверяем, что все переменные из шаблона присутствуют в контексте
        errors = {}
        
        for variable_name in template_variables:
            if variable_name not in context:
                variable = self.registry.get(variable_name)
                
                if variable and variable.required:
                    errors[variable_name] = f"Переменная {variable_name} обязательна"
        
        # Проверяем значения переменных
        for name, value in context.items():
            variable = self.registry.get(name)
            
            if variable:
                valid, error = variable.validate(value)
                
                if not valid:
                    errors[name] = error
        
        return len(errors) == 0, errors


class TemplateParser:
    """
    Парсер шаблонов.
    
    Парсит шаблоны и подготавливает их к рендерингу.
    """
    
    def __init__(self, variable_parser: Optional[VariableParser] = None):
        """
        Инициализация парсера шаблонов.
        
        Args:
            variable_parser (VariableParser, optional): Парсер переменных.
        """
        self.variable_parser = variable_parser or VariableParser()
    
    def parse(self, template_content: str) -> Dict[str, Any]:
        """
        Парсит шаблон и возвращает информацию о нем.
        
        Args:
            template_content (str): Содержимое шаблона.
        
        Returns:
            Dict[str, Any]: Информация о шаблоне.
        """
        # Извлекаем переменные из шаблона
        variables = self.variable_parser.parse(template_content)
        
        # Возвращаем информацию о шаблоне
        return {
            'variables': list(variables),
            'content': template_content,
        }
    
    def validate(self, template_content: str, context: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Проверяет контекст шаблона.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            Tuple[bool, Dict[str, str]]: Флаг валидности и словарь с ошибками.
        """
        return self.variable_parser.validate(template_content, context)
    
    def prepare_context(self, template_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подготавливает контекст для рендеринга шаблона.
        
        Args:
            template_content (str): Содержимое шаблона.
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            Dict[str, Any]: Подготовленный контекст.
        """
        # Извлекаем переменные из шаблона
        variables = self.variable_parser.parse(template_content)
        
        # Создаем новый контекст
        prepared_context = {}
        
        # Добавляем переменные из контекста
        for variable_name in variables:
            if variable_name in context:
                prepared_context[variable_name] = context[variable_name]
            else:
                # Если переменной нет в контексте, пытаемся получить значение по умолчанию
                variable = self.variable_parser.registry.get(variable_name)
                
                if variable:
                    prepared_context[variable_name] = variable.default_value
        
        return prepared_context

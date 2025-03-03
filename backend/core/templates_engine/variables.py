"""
Переменные шаблонов.

Этот модуль содержит классы для работы с переменными шаблонов.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class TemplateVariable:
    """
    Класс для представления переменной шаблона.
    
    Переменная шаблона имеет имя, тип, значение по умолчанию и описание.
    """
    
    def __init__(
        self,
        name: str,
        var_type: str,
        default_value: Any = None,
        description: str = '',
        required: bool = False,
        choices: Optional[List[Any]] = None,
        validators: Optional[List[Callable]] = None
    ):
        """
        Инициализация переменной шаблона.
        
        Args:
            name (str): Имя переменной.
            var_type (str): Тип переменной (str, int, float, bool, date, datetime, list, dict).
            default_value (Any, optional): Значение по умолчанию.
            description (str, optional): Описание переменной.
            required (bool, optional): Флаг, указывающий, что переменная обязательна.
            choices (List[Any], optional): Список допустимых значений.
            validators (List[Callable], optional): Список валидаторов.
        """
        self.name = name
        self.var_type = var_type
        self.default_value = default_value
        self.description = description
        self.required = required
        self.choices = choices or []
        self.validators = validators or []
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Проверяет значение переменной.
        
        Args:
            value (Any): Значение для проверки.
        
        Returns:
            Tuple[bool, Optional[str]]: Флаг валидности и сообщение об ошибке.
        """
        # Проверяем, что значение не None, если переменная обязательна
        if self.required and value is None:
            return False, f"Переменная {self.name} обязательна"
        
        # Если значение None и переменная не обязательна, пропускаем проверки
        if value is None and not self.required:
            return True, None
        
        # Проверяем тип значения
        if self.var_type == 'str' and not isinstance(value, str):
            return False, f"Переменная {self.name} должна быть строкой"
        elif self.var_type == 'int' and not isinstance(value, int):
            return False, f"Переменная {self.name} должна быть целым числом"
        elif self.var_type == 'float' and not isinstance(value, (int, float)):
            return False, f"Переменная {self.name} должна быть числом"
        elif self.var_type == 'bool' and not isinstance(value, bool):
            return False, f"Переменная {self.name} должна быть логическим значением"
        elif self.var_type == 'list' and not isinstance(value, list):
            return False, f"Переменная {self.name} должна быть списком"
        elif self.var_type == 'dict' and not isinstance(value, dict):
            return False, f"Переменная {self.name} должна быть словарем"
        
        # Проверяем, что значение входит в список допустимых значений
        if self.choices and value not in self.choices:
            return False, f"Значение {value} не входит в список допустимых значений для переменной {self.name}"
        
        # Проверяем значение с помощью валидаторов
        for validator in self.validators:
            try:
                validator(value)
            except Exception as e:
                return False, str(e)
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует переменную в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с информацией о переменной.
        """
        return {
            'name': self.name,
            'type': self.var_type,
            'default_value': self.default_value,
            'description': self.description,
            'required': self.required,
            'choices': self.choices,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateVariable':
        """
        Создает переменную из словаря.
        
        Args:
            data (Dict[str, Any]): Словарь с информацией о переменной.
        
        Returns:
            TemplateVariable: Переменная шаблона.
        """
        return cls(
            name=data['name'],
            var_type=data['type'],
            default_value=data.get('default_value'),
            description=data.get('description', ''),
            required=data.get('required', False),
            choices=data.get('choices'),
        )


class VariableRegistry:
    """
    Реестр переменных шаблона.
    
    Хранит информацию о доступных переменных шаблона.
    """
    
    def __init__(self):
        """
        Инициализация реестра переменных.
        """
        self.variables: Dict[str, TemplateVariable] = {}
    
    def register(self, variable: TemplateVariable) -> None:
        """
        Регистрирует переменную в реестре.
        
        Args:
            variable (TemplateVariable): Переменная для регистрации.
        """
        self.variables[variable.name] = variable
    
    def unregister(self, name: str) -> None:
        """
        Удаляет переменную из реестра.
        
        Args:
            name (str): Имя переменной.
        """
        if name in self.variables:
            del self.variables[name]
    
    def get(self, name: str) -> Optional[TemplateVariable]:
        """
        Возвращает переменную по имени.
        
        Args:
            name (str): Имя переменной.
        
        Returns:
            Optional[TemplateVariable]: Переменная или None, если переменная не найдена.
        """
        return self.variables.get(name)
    
    def get_all(self) -> Dict[str, TemplateVariable]:
        """
        Возвращает все переменные.
        
        Returns:
            Dict[str, TemplateVariable]: Словарь с переменными.
        """
        return self.variables.copy()
    
    def validate_context(self, context: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Проверяет контекст шаблона.
        
        Args:
            context (Dict[str, Any]): Контекст шаблона.
        
        Returns:
            Tuple[bool, Dict[str, str]]: Флаг валидности и словарь с ошибками.
        """
        errors = {}
        
        # Проверяем, что все обязательные переменные присутствуют
        for name, variable in self.variables.items():
            if variable.required and name not in context:
                errors[name] = f"Переменная {name} обязательна"
        
        # Проверяем значения переменных
        for name, value in context.items():
            variable = self.variables.get(name)
            
            if variable:
                valid, error = variable.validate(value)
                
                if not valid:
                    errors[name] = error
        
        return len(errors) == 0, errors
    
    def extract_variables_from_template(self, template_content: str) -> Set[str]:
        """
        Извлекает имена переменных из шаблона.
        
        Args:
            template_content (str): Содержимое шаблона.
        
        Returns:
            Set[str]: Множество имен переменных.
        """
        # Регулярное выражение для поиска переменных в шаблоне
        # Поддерживает форматы {{ variable }}, {{ variable.attribute }}, {{ variable|filter }}
        pattern = r'{{\s*([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9_]+|\|[a-zA-Z0-9_]+(?:\([^)]*\))?)*\s*}}'
        
        # Находим все переменные в шаблоне
        matches = re.findall(pattern, template_content)
        
        # Возвращаем множество уникальных имен переменных
        return set(matches)
    
    def get_missing_variables(self, template_content: str) -> Set[str]:
        """
        Возвращает имена переменных, которые используются в шаблоне, но не зарегистрированы.
        
        Args:
            template_content (str): Содержимое шаблона.
        
        Returns:
            Set[str]: Множество имен переменных.
        """
        # Извлекаем имена переменных из шаблона
        template_variables = self.extract_variables_from_template(template_content)
        
        # Находим переменные, которые не зарегистрированы
        missing_variables = template_variables - set(self.variables.keys())
        
        return missing_variables

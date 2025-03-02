"""
Парсер документации из docstrings.

Этот модуль предоставляет функциональность для извлечения информации
из докстрингов Python и преобразования их в структурированный формат
для использования в документации API.
"""

import re
import inspect
from typing import Dict, List, Any, Optional, Tuple, Callable


class DocstringParser:
    """
    Парсер для извлечения информации из докстрингов.

    Извлекает описание, параметры, возвращаемые значения и примеры
    из докстрингов в формате Google, ReStructuredText или NumPy.
    """

    # Регулярные выражения для разбора разделов докстрингов
    SECTION_REGEX = re.compile(r'^(?P<name>[A-Za-z_]+):\s*$|^(?P<name2>[A-Za-z_]+)\s*$')
    PARAM_REGEX = re.compile(r'^(?P<name>\w+)\s*(\((?P<type>[^)]+)\))?\s*:\s*(?P<desc>.+)$')
    RETURNS_REGEX = re.compile(r'^(?P<type>[^:]+):\s*(?P<desc>.+)$')

    def __init__(self):
        """
        Инициализирует парсер докстрингов.
        """
        self.supported_sections = {
            'Args': self._parse_params,
            'Arguments': self._parse_params,
            'Params': self._parse_params,
            'Parameters': self._parse_params,
            'Returns': self._parse_returns,
            'Return': self._parse_returns,
            'Raises': self._parse_raises,
            'Exceptions': self._parse_raises,
            'Example': self._parse_example,
            'Examples': self._parse_example,
        }

    def parse(self, docstring: str) -> Dict[str, Any]:
        """
        Парсит докстринг и возвращает структурированную информацию.

        Аргументы:
            docstring: Докстринг для разбора.

        Возвращает:
            Словарь с извлеченной информацией из докстринга.
        """
        if not docstring:
            return {}

        # Удаление лишних пробелов и переводов строк
        docstring = inspect.cleandoc(docstring)

        # Результирующий словарь
        result = {
            'description': '',
            'params': [],
            'returns': {},
            'raises': [],
            'examples': []
        }

        # Разбор докстринга по секциям
        current_section = 'description'
        section_content = []

        lines = docstring.split('\n')
        for i, line in enumerate(lines):
            # Проверка на начало новой секции
            section_match = self.SECTION_REGEX.match(line)

            if section_match and (section_match.group('name') in self.supported_sections or
                                  section_match.group('name2') in self.supported_sections):
                # Обработка предыдущей секции
                self._process_section(result, current_section, section_content)

                # Начало новой секции
                section_name = section_match.group('name') or section_match.group('name2')
                current_section = section_name
                section_content = []
            else:
                section_content.append(line)

        # Обработка последней секции
        self._process_section(result, current_section, section_content)

        return result

    def _process_section(self, result: Dict[str, Any], section_name: str, content: List[str]) -> None:
        """
        Обрабатывает содержимое раздела докстринга.

        Аргументы:
            result: Словарь результатов для обновления.
            section_name: Имя раздела.
            content: Содержимое раздела в виде списка строк.
        """
        if not content:
            return

        content_text = '\n'.join(content).strip()

        if section_name == 'description':
            result['description'] = content_text
        elif section_name in self.supported_sections:
            parser = self.supported_sections[section_name]
            parser(result, content)

    def _parse_params(self, result: Dict[str, Any], content: List[str]) -> None:
        """
        Разбор раздела параметров.

        Аргументы:
            result: Словарь результатов для обновления.
            content: Содержимое раздела в виде списка строк.
        """
        current_param = None
        description_lines = []

        for line in content:
            line = line.strip()
            if not line:
                continue

            param_match = self.PARAM_REGEX.match(line)
            if param_match:
                # Сохранение предыдущего параметра, если он есть
                if current_param:
                    current_param['description'] = '\n'.join(description_lines).strip()
                    result['params'].append(current_param)
                    description_lines = []

                # Новый параметр
                current_param = {
                    'name': param_match.group('name'),
                    'type': param_match.group('type') or '',
                    'description': param_match.group('desc') or ''
                }

                # Если описание уже есть в одной строке, сразу добавляем параметр
                if current_param['description']:
                    result['params'].append(current_param)
                    current_param = None
            elif current_param:
                description_lines.append(line)

        # Добавление последнего параметра
        if current_param:
            if description_lines:
                current_param['description'] = '\n'.join(description_lines).strip()
            result['params'].append(current_param)

    def _parse_returns(self, result: Dict[str, Any], content: List[str]) -> None:
        """
        Разбор раздела возвращаемых значений.

        Аргументы:
            result: Словарь результатов для обновления.
            content: Содержимое раздела в виде списка строк.
        """
        full_content = '\n'.join(content).strip()
        returns_match = self.RETURNS_REGEX.match(full_content)

        if returns_match:
            result['returns'] = {
                'type': returns_match.group('type').strip(),
                'description': returns_match.group('desc').strip()
            }
        else:
            result['returns'] = {
                'type': '',
                'description': full_content
            }

    def _parse_raises(self, result: Dict[str, Any], content: List[str]) -> None:
        """
        Разбор раздела исключений.

        Аргументы:
            result: Словарь результатов для обновления.
            content: Содержимое раздела в виде списка строк.
        """
        current_exception = None
        description_lines = []

        for line in content:
            line = line.strip()
            if not line:
                continue

            parts = line.split(':', 1)
            if len(parts) == 2 and ' ' not in parts[0]:
                # Сохранение предыдущего исключения, если оно есть
                if current_exception:
                    current_exception['description'] = '\n'.join(description_lines).strip()
                    result['raises'].append(current_exception)
                    description_lines = []

                # Новое исключение
                current_exception = {
                    'type': parts[0].strip(),
                    'description': parts[1].strip()
                }

                # Если описание уже есть в одной строке, сразу добавляем исключение
                if current_exception['description']:
                    result['raises'].append(current_exception)
                    current_exception = None
            elif current_exception:
                description_lines.append(line)
            else:
                # Если формат не соответствует ожидаемому, просто добавляем строку как тип
                result['raises'].append({
                    'type': line,
                    'description': ''
                })

        # Добавление последнего исключения
        if current_exception:
            if description_lines:
                current_exception['description'] = '\n'.join(description_lines).strip()
            result['raises'].append(current_exception)

    def _parse_example(self, result: Dict[str, Any], content: List[str]) -> None:
        """
        Разбор раздела примеров.

        Аргументы:
            result: Словарь результатов для обновления.
            content: Содержимое раздела в виде списка строк.
        """
        example_text = '\n'.join(content).strip()
        if example_text:
            result['examples'].append(example_text)


def parse_docstring(obj: Callable) -> Dict[str, Any]:
    """
    Парсит докстринг объекта (функции, метода или класса).

    Аргументы:
        obj: Объект, докстринг которого нужно распарсить.

    Возвращает:
        Словарь с информацией из докстринга.
    """
    parser = DocstringParser()
    docstring = inspect.getdoc(obj)
    return parser.parse(docstring)
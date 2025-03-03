"""
Движок шаблонов.

Этот пакет содержит компоненты для работы с шаблонами, включая парсеры, рендереры и переменные.
"""

from core.templates_engine.parsers import TemplateParser, VariableParser
from core.templates_engine.variables import TemplateVariable, VariableRegistry
from core.templates_engine.renderers import (
    BaseTemplateRenderer, HTMLTemplateRenderer, PDFTemplateRenderer, DocxTemplateRenderer
)


__all__ = [
    'TemplateParser',
    'VariableParser',
    'TemplateVariable',
    'VariableRegistry',
    'BaseTemplateRenderer',
    'HTMLTemplateRenderer',
    'PDFTemplateRenderer',
    'DocxTemplateRenderer',
]

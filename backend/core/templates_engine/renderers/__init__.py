"""
Рендереры шаблонов.

Этот пакет содержит рендереры для шаблонов.
"""

from core.templates_engine.renderers.base import BaseTemplateRenderer
from core.templates_engine.renderers.html_renderer import HTMLTemplateRenderer
from core.templates_engine.renderers.pdf_renderer import PDFTemplateRenderer
from core.templates_engine.renderers.docx_renderer import DocxTemplateRenderer


__all__ = [
    'BaseTemplateRenderer',
    'HTMLTemplateRenderer',
    'PDFTemplateRenderer',
    'DocxTemplateRenderer',
]

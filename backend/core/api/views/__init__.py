"""
Пакет представлений API Core.

Этот пакет содержит все представления для API модуля Core,
включая представления для настроек и тегов.
"""

from core.api.views.settings import SettingViewSet
from core.api.views.tags import TagViewSet, TaggedItemViewSet

__all__ = [
    # Представления для настроек
    'SettingViewSet',

    # Представления для тегов
    'TagViewSet',
    'TaggedItemViewSet',
]
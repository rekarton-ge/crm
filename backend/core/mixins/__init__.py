"""
Миксины для моделей и представлений.

Этот пакет содержит миксины для моделей Django и представлений Django REST Framework.
"""

from core.mixins.model_mixins import (
    TimeStampedMixin, UUIDMixin, SoftDeleteMixin, ActiveMixin,
    OrderableMixin, SlugMixin, DescriptionMixin, MetadataMixin
)

from core.mixins.view_mixins import (
    MultiSerializerMixin, ReadWriteSerializerMixin, SoftDeleteViewMixin,
    RestoreViewMixin, ActivateDeactivateViewMixin, FilterByUserMixin,
    FilterByOwnerMixin, HistoryViewMixin, MetadataViewMixin
)


__all__ = [
    # Миксины для моделей
    'TimeStampedMixin',
    'UUIDMixin',
    'SoftDeleteMixin',
    'ActiveMixin',
    'OrderableMixin',
    'SlugMixin',
    'DescriptionMixin',
    'MetadataMixin',
    
    # Миксины для представлений
    'MultiSerializerMixin',
    'ReadWriteSerializerMixin',
    'SoftDeleteViewMixin',
    'RestoreViewMixin',
    'ActivateDeactivateViewMixin',
    'FilterByUserMixin',
    'FilterByOwnerMixin',
    'HistoryViewMixin',
    'MetadataViewMixin',
]

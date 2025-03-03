# Импортируем обработчики сигналов для их регистрации
from accounts.signals.handlers import (
    create_user_profile, save_user_profile,
    log_role_assignment, log_role_removal
)

__all__ = [
    'create_user_profile',
    'save_user_profile',
    'log_role_assignment',
    'log_role_removal',
]
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    """
    Конфигурация приложения accounts.
    """
    name = 'accounts'
    verbose_name = _('Управление пользователями')

    def ready(self):
        """
        Выполняется при загрузке приложения.
        Здесь импортируем сигналы, чтобы они были зарегистрированы.
        """
        try:
            # Импортируем обработчики сигналов
            import accounts.signals.handlers  # noqa

            # Логи запуска приложения (опционально)
            import logging
            logger = logging.getLogger(__name__)
            logger.debug('Приложение accounts успешно инициализировано')

        except ImportError as e:
            # В случае ошибки импорта логируем ее, но позволяем приложению запуститься
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка при инициализации приложения accounts: {e}')
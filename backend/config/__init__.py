# Импортируем Celery при запуске приложения
from .celery import app as celery_app

__all__ = ('celery_app',)
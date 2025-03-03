from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from accounts.models import UserSession
from datetime import timedelta


class Command(BaseCommand):
    """
    Команда для очистки устаревших токенов и сессий пользователей.

    Очищает:
    - Завершенные сессии старше определенного срока
    - Неактивные сессии (без последней активности за определенный период)
    """
    help = _('Очищает устаревшие токены и сессии пользователей')

    def add_arguments(self, parser):
        """
        Добавляет аргументы командной строки.
        """
        parser.add_argument(
            '--days-old',
            dest='days_old',
            type=int,
            default=30,
            help=_('Удалять завершенные сессии старше указанного количества дней (по умолчанию 30)'),
        )
        parser.add_argument(
            '--inactive-days',
            dest='inactive_days',
            type=int,
            default=7,
            help=_('Завершать сессии без активности за указанное количество дней (по умолчанию 7)'),
        )
        parser.add_argument(
            '--dry-run',
            dest='dry_run',
            action='store_true',
            default=False,
            help=_('Только показать, что будет удалено, без фактического удаления'),
        )

    def handle(self, *args, **options):
        """
        Основной метод команды.
        """
        days_old = options['days_old']
        inactive_days = options['inactive_days']
        dry_run = options['dry_run']

        # Текущая дата и время
        now = timezone.now()

        # Дата, старше которой удаляем завершенные сессии
        old_date = now - timedelta(days=days_old)

        # Дата, после которой считаем сессии неактивными
        inactive_date = now - timedelta(days=inactive_days)

        # Находим завершенные сессии для удаления
        old_ended_sessions = UserSession.objects.filter(
            ended_at__lt=old_date
        )
        old_ended_count = old_ended_sessions.count()

        # Находим неактивные сессии для завершения
        inactive_sessions = UserSession.objects.filter(
            ended_at=None,
            last_activity__lt=inactive_date
        )
        inactive_count = inactive_sessions.count()

        # Выводим информацию
        self.stdout.write(self.style.NOTICE(
            _("Найдено %(count)d завершенных сессий старше %(days)d дней") % {
                'count': old_ended_count,
                'days': days_old
            }
        ))

        self.stdout.write(self.style.NOTICE(
            _("Найдено %(count)d неактивных сессий без активности более %(days)d дней") % {
                'count': inactive_count,
                'days': inactive_days
            }
        ))

        # Если это не сухой запуск, выполняем действия
        if not dry_run:
            # Удаляем старые завершенные сессии
            if old_ended_count > 0:
                old_ended_sessions.delete()
                self.stdout.write(self.style.SUCCESS(
                    _("Удалено %(count)d завершенных сессий") % {
                        'count': old_ended_count
                    }
                ))

            # Завершаем неактивные сессии
            if inactive_count > 0:
                for session in inactive_sessions:
                    session.end_session()

                self.stdout.write(self.style.SUCCESS(
                    _("Завершено %(count)d неактивных сессий") % {
                        'count': inactive_count
                    }
                ))
        else:
            self.stdout.write(self.style.WARNING(
                _("Режим проверки (--dry-run). Никаких изменений не было внесено.")
            ))

        # Очистка токенов из blacklist в rest_framework_simplejwt (если установлен)
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            from django.db import connection

            # Получаем имя таблицы из модели
            token_table_name = OutstandingToken._meta.db_table
            blacklist_table_name = BlacklistedToken._meta.db_table

            # Проверяем, существуют ли таблицы
            with connection.cursor() as cursor:
                # Для PostgreSQL
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{token_table_name}'
                    );
                """)
                token_table_exists = cursor.fetchone()[0]

                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{blacklist_table_name}'
                    );
                """)
                blacklist_table_exists = cursor.fetchone()[0]

            if token_table_exists and blacklist_table_exists:
                # Находим устаревшие токены (старше days_old дней)
                expired_tokens = OutstandingToken.objects.filter(
                    expires_at__lt=now
                )
                expired_count = expired_tokens.count()

                # Находим токены в черном списке для устаревших токенов
                blacklisted_tokens = BlacklistedToken.objects.filter(
                    token__expires_at__lt=now
                )
                blacklisted_count = blacklisted_tokens.count()

                self.stdout.write(self.style.NOTICE(
                    _("Найдено %(count)d устаревших токенов") % {
                        'count': expired_count
                    }
                ))

                self.stdout.write(self.style.NOTICE(
                    _("Найдено %(count)d токенов в черном списке для устаревших токенов") % {
                        'count': blacklisted_count
                    }
                ))

                if not dry_run:
                    # Сначала удаляем записи из черного списка
                    if blacklisted_count > 0:
                        blacklisted_tokens.delete()
                        self.stdout.write(self.style.SUCCESS(
                            _("Удалено %(count)d токенов из черного списка") % {
                                'count': blacklisted_count
                            }
                        ))

                    # Затем удаляем сами токены
                    if expired_count > 0:
                        expired_tokens.delete()
                        self.stdout.write(self.style.SUCCESS(
                            _("Удалено %(count)d устаревших токенов") % {
                                'count': expired_count
                            }
                        ))

        except ImportError:
            self.stdout.write(self.style.WARNING(
                _("Модуль rest_framework_simplejwt.token_blacklist не найден. Пропускаем очистку токенов JWT.")
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                _("Ошибка при очистке токенов JWT: %(error)s") % {
                    'error': str(e)
                }
            ))

        # Итог
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                _("Проверка завершена. Запустите команду без --dry-run для выполнения очистки.")
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                _("Очистка успешно завершена.")
            ))
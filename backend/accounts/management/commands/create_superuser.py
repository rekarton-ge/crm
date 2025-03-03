import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.models import Role, RoleAssignment

User = get_user_model()


class Command(BaseCommand):
    """
    Команда для создания суперпользователя с дополнительными параметрами.

    Отличается от стандартной команды createsuperuser тем, что позволяет:
    - Указать дополнительные поля модели User
    - Автоматически назначить роль 'Администратор'
    - Проверить сложность пароля
    """
    help = _('Создает суперпользователя и назначает ему роль Администратора')

    def add_arguments(self, parser):
        """
        Добавляет аргументы командной строки.
        """
        parser.add_argument(
            '--username',
            dest='username',
            default=None,
            help=_('Имя пользователя для суперпользователя'),
        )
        parser.add_argument(
            '--email',
            dest='email',
            default=None,
            help=_('Email для суперпользователя'),
        )
        parser.add_argument(
            '--first-name',
            dest='first_name',
            default='',
            help=_('Имя суперпользователя'),
        )
        parser.add_argument(
            '--last-name',
            dest='last_name',
            default='',
            help=_('Фамилия суперпользователя'),
        )
        parser.add_argument(
            '--phone',
            dest='phone_number',
            default=None,
            help=_('Номер телефона суперпользователя'),
        )
        parser.add_argument(
            '--password',
            dest='password',
            default=None,
            help=_('Пароль суперпользователя (если не указан, будет запрошен интерактивно)'),
        )
        parser.add_argument(
            '--no-admin-role',
            dest='no_admin_role',
            action='store_true',
            default=False,
            help=_('Не назначать роль Администратора'),
        )
        parser.add_argument(
            '--force',
            dest='force',
            action='store_true',
            default=False,
            help=_('Пересоздать пользователя, если он уже существует'),
        )

    def handle(self, *args, **options):
        """
        Основной метод команды.
        """
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone_number = options['phone_number']
        no_admin_role = options['no_admin_role']
        force = options['force']

        # Если имя пользователя не указано, запрашиваем его интерактивно
        if not username:
            while not username:
                username = input(_("Имя пользователя: "))

        # Проверяем существование пользователя
        if User.objects.filter(username=username).exists():
            if force:
                User.objects.filter(username=username).delete()
                self.stdout.write(self.style.WARNING(
                    _("Пользователь с именем '%(username)s' удален для повторного создания.") % {
                        'username': username
                    }
                ))
            else:
                raise CommandError(
                    _("Пользователь с именем '%(username)s' уже существует. Используйте --force для пересоздания.") % {
                        'username': username
                    }
                )

        # Если email не указан, запрашиваем его интерактивно
        if not email:
            while not email:
                email = input(_("Email: "))

        # Проверяем существование email
        if User.objects.filter(email=email).exists():
            if force:
                # Если не удаляем пользователя с уже существующим email
                if not User.objects.filter(username=username, email=email).exists():
                    raise CommandError(
                        _("Пользователь с email '%(email)s' уже существует.") % {
                            'email': email
                        }
                    )
            else:
                raise CommandError(
                    _("Пользователь с email '%(email)s' уже существует.") % {
                        'email': email
                    }
                )

        # Если пароль не указан, запрашиваем его интерактивно
        if not password:
            password = getpass.getpass(_("Пароль: "))
            password2 = getpass.getpass(_("Подтверждение пароля: "))
            if password != password2:
                raise CommandError(_("Пароли не совпадают."))

        # Проверяем сложность пароля
        if len(password) < 8:
            raise CommandError(_("Пароль должен содержать минимум 8 символов."))

        # Создаем суперпользователя
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            self.stdout.write(self.style.SUCCESS(
                _("Суперпользователь '%(username)s' успешно создан.") % {
                    'username': username
                }
            ))

            # Назначаем роль Администратора, если нужно
            if not no_admin_role:
                try:
                    # Получаем или создаем роль Администратора
                    admin_role, created = Role.objects.get_or_create(
                        name=_("Администратор"),
                        defaults={
                            'description': _("Полный доступ ко всем функциям системы"),
                            'is_system': True
                        }
                    )

                    # Назначаем роль пользователю
                    RoleAssignment.objects.create(
                        user=user,
                        role=admin_role
                    )

                    self.stdout.write(self.style.SUCCESS(
                        _("Роль 'Администратор' успешно назначена пользователю '%(username)s'.") % {
                            'username': username
                        }
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        _("Ошибка при назначении роли: %(error)s") % {
                            'error': str(e)
                        }
                    ))

        except Exception as e:
            raise CommandError(
                _("Ошибка при создании суперпользователя: %(error)s") % {
                    'error': str(e)
                }
            )
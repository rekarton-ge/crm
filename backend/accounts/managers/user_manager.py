from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей, расширяющий стандартный BaseUserManager Django.
    Позволяет аутентифицироваться по имени пользователя или email и добавляет
    дополнительные методы для работы с пользователями.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя с указанными username, email и паролем.

        Args:
            username (str): Имя пользователя
            email (str): Email пользователя
            password (str, optional): Пароль. По умолчанию None
            **extra_fields: Дополнительные поля пользователя

        Returns:
            User: Созданный пользователь

        Raises:
            ValueError: Если не указан username или email
        """
        if not username:
            raise ValueError(_('Имя пользователя обязательно'))
        if not email:
            raise ValueError(_('Email обязателен'))

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Создает и сохраняет суперпользователя с указанными username, email и паролем.

        Args:
            username (str): Имя пользователя
            email (str): Email пользователя
            password (str, optional): Пароль. По умолчанию None
            **extra_fields: Дополнительные поля пользователя

        Returns:
            User: Созданный суперпользователь

        Raises:
            ValueError: Если указаны is_staff=False или is_superuser=False
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_superuser=True'))

        return self.create_user(username, email, password, **extra_fields)

    def get_by_natural_key(self, username):
        """
        Переопределяет метод получения пользователя по естественному ключу.
        Позволяет выполнять аутентификацию как по имени пользователя, так и по email.

        Args:
            username (str): Имя пользователя или email

        Returns:
            User: Найденный пользователь

        Raises:
            User.DoesNotExist: Если пользователь не найден
        """
        return self.get(Q(username=username) | Q(email__iexact=username))

    def get_active_users(self):
        """
        Возвращает только активных пользователей.

        Returns:
            QuerySet: QuerySet с активными пользователями
        """
        return self.filter(is_active=True)

    def get_staff_users(self):
        """
        Возвращает только пользователей со статусом персонала.

        Returns:
            QuerySet: QuerySet с пользователями из персонала
        """
        return self.filter(is_staff=True)

    def get_users_by_role(self, role_name):
        """
        Возвращает пользователей с указанной ролью.

        Args:
            role_name (str): Название роли

        Returns:
            QuerySet: QuerySet с пользователями, имеющими указанную роль
        """
        return self.filter(roles__name=role_name)

    def get_locked_users(self):
        """
        Возвращает пользователей с заблокированными аккаунтами.

        Returns:
            QuerySet: QuerySet с заблокированными пользователями
        """
        from django.utils import timezone
        return self.filter(account_locked_until__gt=timezone.now())

    def search_users(self, query):
        """
        Ищет пользователей по имени пользователя, email, имени или фамилии.

        Args:
            query (str): Поисковый запрос

        Returns:
            QuerySet: QuerySet с найденными пользователями
        """
        return self.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        ).distinct()
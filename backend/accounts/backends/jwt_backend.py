from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


class JWTBackend(ModelBackend):
    """
    Бэкенд аутентификации для JWT токенов.
    Позволяет аутентифицироваться по имени пользователя или email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Аутентифицирует пользователя по имени пользователя/email и паролю.
        """
        if username is None or password is None:
            return None

        try:
            # Ищем пользователя по имени пользователя или email
            user = User.objects.get(Q(username=username) | Q(email=username))

            # Проверяем, не заблокирован ли аккаунт
            if user.is_locked():
                return None

            # Проверяем пароль
            if user.check_password(password) and self.user_can_authenticate(user):
                # Сбрасываем счетчик неудачных попыток входа
                user.reset_failed_login_attempts()

                return user
            else:
                # Увеличиваем счетчик неудачных попыток входа
                user.increment_failed_login_attempts()

                return None

        except User.DoesNotExist:
            # Не возвращаем ошибку о несуществующем пользователе
            # для безопасности
            return None

    def user_can_authenticate(self, user):
        """
        Проверяет, может ли пользователь аутентифицироваться.
        """
        # Проверяем активность пользователя
        is_active = getattr(user, 'is_active', False)

        # Проверяем блокировку пользователя
        is_locked = False
        locked_until = getattr(user, 'account_locked_until', None)
        if locked_until and locked_until > timezone.now():
            is_locked = True

        return is_active and not is_locked
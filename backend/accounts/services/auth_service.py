from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import UserSession, LoginAttempt, UserActivity


class AuthService:
    """
    Сервисный класс для аутентификации, авторизации, создания и проверки токенов.
    """

    @staticmethod
    def authenticate_user(username, password, request=None):
        """
        Аутентифицирует пользователя по имени пользователя/email и паролю.
        """
        from django.contrib.auth import authenticate

        # Получаем данные запроса для логирования
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Пытаемся аутентифицировать пользователя
        user = authenticate(username=username, password=password)

        # Логируем попытку входа
        if user is not None:
            # Успешная аутентификация
            if user.is_active:
                user.reset_failed_login_attempts()
                LoginAttempt.log_login_attempt(
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    was_successful=True
                )
                return user
            else:
                # Пользователь неактивен
                LoginAttempt.log_login_attempt(
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    was_successful=False,
                    failure_reason='account_disabled'
                )
                return None
        else:
            # Неудачная аутентификация
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Пытаемся найти пользователя
            try:
                if '@' in username:
                    user = User.objects.get(email=username)
                else:
                    user = User.objects.get(username=username)

                # Пользователь существует, но пароль неверный
                user.increment_failed_login_attempts()

                if user.is_locked():
                    failure_reason = 'account_locked'
                else:
                    failure_reason = 'invalid_password'
            except User.DoesNotExist:
                # Пользователь не найден
                failure_reason = 'user_not_found'

            LoginAttempt.log_login_attempt(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                was_successful=False,
                failure_reason=failure_reason
            )
            return None

    @staticmethod
    def generate_tokens(user):
        """
        Генерирует токены доступа и обновления для пользователя.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def create_user_session(user, request, token_key):
        """
        Создает запись о сессии пользователя.
        """
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Определение типа устройства
        device_type = 'other'
        if user_agent:
            if 'Mobile' in user_agent:
                device_type = 'mobile'
            elif 'Tablet' in user_agent:
                device_type = 'tablet'
            else:
                device_type = 'desktop'

        # Создание сессии
        session = UserSession.objects.create(
            user=user,
            session_key=token_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type
        )

        # Логирование активности
        UserActivity.log_activity(
            user=user,
            session=session,
            activity_type='login',
            description='Вход в систему',
            ip_address=ip_address
        )

        return session

    @staticmethod
    def end_user_session(token_key):
        """
        Завершает сессию пользователя.
        """
        try:
            session = UserSession.objects.get(session_key=token_key)
            session.end_session()

            # Логирование активности
            UserActivity.log_activity(
                user=session.user,
                session=session,
                activity_type='logout',
                description='Выход из системы',
                ip_address=session.ip_address
            )

            return True
        except UserSession.DoesNotExist:
            return False

    @staticmethod
    def get_active_sessions(user):
        """
        Возвращает активные сессии пользователя.
        """
        return UserSession.get_active_sessions(user)

    @staticmethod
    def end_all_sessions(user, current_session_key=None):
        """
        Завершает все сессии пользователя, кроме текущей.
        """
        sessions = UserSession.get_active_sessions(user)

        if current_session_key:
            sessions = sessions.exclude(session_key=current_session_key)

        for session in sessions:
            session.end_session()

            # Логирование активности
            UserActivity.log_activity(
                user=user,
                activity_type='logout',
                description='Сессия завершена администратором',
                ip_address=session.ip_address
            )

        return sessions.count()

    @staticmethod
    def update_last_login(user):
        """
        Обновляет время последнего входа пользователя.
        """
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
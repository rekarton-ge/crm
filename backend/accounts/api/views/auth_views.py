from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.api.serializers import (
    LoginSerializer, UserDetailSerializer, TokenRefreshSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from accounts.services import AuthService
from accounts.models import UserSession

User = get_user_model()


class LoginView(views.APIView):
    """
    Представление для аутентификации пользователя и получения JWT-токена.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Аутентифицируем пользователя
        user = AuthService.authenticate_user(username, password, request)

        if user is None:
            return Response(
                {"error": _("Неверное имя пользователя или пароль.")},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Проверяем, не заблокирован ли аккаунт
        if user.is_locked():
            return Response(
                {"error": _("Ваш аккаунт временно заблокирован из-за превышения количества попыток входа.")},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Генерируем токены
        tokens = AuthService.generate_tokens(user)

        # Создаем запись о сессии
        AuthService.create_user_session(user, request, tokens['refresh'])

        # Обновляем время последнего входа
        AuthService.update_last_login(user)

        # Сериализуем пользователя для ответа
        user_serializer = UserDetailSerializer(user)

        return Response({
            "access_token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "user": user_serializer.data
        })


class LogoutView(views.APIView):
    """
    Представление для выхода из системы (инвалидация токена).
    """

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            # Инвалидируем токен обновления
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Завершаем сессию пользователя
            AuthService.end_user_session(refresh_token)

            return Response({"message": _("Успешный выход из системы.")})
        except TokenError:
            return Response(
                {"error": _("Недействительный или просроченный токен.")},
                status=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(views.APIView):
    """
    Представление для обновления токена доступа.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            # Создаем объект токена обновления
            token = RefreshToken(refresh_token)

            return Response({
                "access_token": str(token.access_token)
            })
        except TokenError:
            return Response(
                {"error": _("Недействительный или просроченный токен.")},
                status=status.HTTP_400_BAD_REQUEST
            )


class SessionListView(views.APIView):
    """
    Представление для получения списка активных сессий пользователя.
    """

    def get(self, request, *args, **kwargs):
        user = request.user

        # Получаем активные сессии пользователя
        sessions = AuthService.get_active_sessions(user)

        # Подготавливаем данные для ответа
        current_token = request.auth.payload.get('jti', '')

        session_data = []
        for session in sessions:
            session_data.append({
                "id": session.id,
                "device_type": session.device_type,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "location": session.location,
                "started_at": session.started_at,
                "last_activity": session.last_activity,
                "is_current": session.session_key == current_token
            })

        return Response(session_data)


class SessionEndView(views.APIView):
    """
    Представление для завершения конкретной сессии пользователя.
    """

    def delete(self, request, pk=None, *args, **kwargs):
        user = request.user

        try:
            # Проверяем, что сессия принадлежит пользователю
            session = UserSession.objects.get(id=pk, user=user)

            # Запрещаем завершение текущей сессии через этот эндпоинт
            current_token = request.auth.payload.get('jti', '')
            if session.session_key == current_token:
                return Response(
                    {"error": _("Нельзя завершить текущую сессию через этот эндпоинт. Используйте /api/auth/logout/.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Завершаем сессию
            session.end_session()

            return Response({"message": _("Сессия завершена.")})
        except UserSession.DoesNotExist:
            return Response(
                {"error": _("Сессия не найдена или не принадлежит пользователю.")},
                status=status.HTTP_404_NOT_FOUND
            )


class AllSessionsEndView(views.APIView):
    """
    Представление для завершения всех сессий пользователя, кроме текущей.
    """

    def delete(self, request, *args, **kwargs):
        user = request.user
        current_token = request.auth.payload.get('jti', '')

        # Завершаем все сессии, кроме текущей
        count = AuthService.end_all_sessions(user, current_token)

        return Response({
            "message": _("Все другие сессии завершены."),
            "session_count": count
        })


class PasswordChangeView(views.APIView):
    """
    Представление для изменения пароля пользователя.
    """

    def post(self, request, *args, **kwargs):
        from accounts.api.serializers import ChangePasswordSerializer

        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data['new_password']

        # Изменяем пароль
        from accounts.services import UserService
        UserService.change_password(user, new_password)

        # Завершаем все другие сессии
        current_token = request.auth.payload.get('jti', '')
        AuthService.end_all_sessions(user, current_token)

        return Response({"message": _("Пароль успешно изменен.")})


class PasswordResetRequestView(views.APIView):
    """
    Представление для запроса сброса пароля.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Проверяем существование пользователя
        try:
            user = User.objects.get(email=email)

            # Генерируем токен и отправляем письмо
            # (реализация этой функциональности будет в auth_service.py)
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # В реальном проекте здесь должна быть отправка письма
            # AuthService.send_password_reset_email(user, uid, token)

            return Response({"message": _("Инструкции по сбросу пароля отправлены на указанный email.")})

        except User.DoesNotExist:
            # Для безопасности возвращаем такой же ответ, даже если пользователь не найден
            return Response({"message": _("Инструкции по сбросу пароля отправлены на указанный email.")})


class PasswordResetConfirmView(views.APIView):
    """
    Представление для подтверждения сброса пароля.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        # В реальном проекте здесь должна быть проверка токена
        # и установка нового пароля для пользователя
        # success = AuthService.reset_password_with_token(token, password)

        # Заглушка для примера
        success = True

        if success:
            return Response({"message": _("Пароль успешно изменен.")})
        else:
            return Response(
                {"error": _("Недействительный или просроченный токен сброса пароля.")},
                status=status.HTTP_400_BAD_REQUEST
            )
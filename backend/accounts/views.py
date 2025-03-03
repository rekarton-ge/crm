"""
Представления для приложения accounts.
"""

from rest_framework import status, generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from accounts.serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserSessionSerializer,
    LoginSerializer,
    RegisterSerializer
)
from accounts.models import UserSession, LoginAttempt


class LoginView(APIView):
    """
    Представление для входа в систему.
    """
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            # Создаем запись о попытке входа
            LoginAttempt.objects.create(
                username=user.username,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                was_successful=True
            )
            
            # Создаем сессию
            UserSession.objects.create(
                user=user,
                session_key=str(refresh),
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_type='other'
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        except serializers.ValidationError as e:
            # Создаем запись о неудачной попытке входа
            LoginAttempt.objects.create(
                username=request.data.get('username', ''),
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                was_successful=False
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """
    Представление для регистрации пользователей.
    """
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Представление для работы с профилем пользователя.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserSessionListView(generics.ListAPIView):
    """
    Представление для просмотра сессий пользователя.
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user,
            ended_at__isnull=True
        )


class UserSessionDetailView(generics.DestroyAPIView):
    """
    Представление для завершения конкретной сессии.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.ended_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EndAllSessionsView(APIView):
    """
    Представление для завершения всех сессий пользователя.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserSession.objects.filter(
            user=request.user,
            ended_at__isnull=True
        ).update(ended_at=timezone.now())
        return Response({"message": "Все сессии завершены"}) 
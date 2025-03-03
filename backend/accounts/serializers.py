"""
Сериализаторы для приложения accounts.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from accounts.models import UserSession, UserActivity, Profile
from accounts.utils.password_utils import validate_user_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')
        read_only_fields = ('id', 'is_active')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя.
    """
    position = serializers.CharField(source='profile.position', required=False)
    department = serializers.CharField(source='profile.department', required=False)
    bio = serializers.CharField(source='profile.bio', required=False)
    date_of_birth = serializers.DateField(source='profile.date_of_birth', required=False)
    avatar = serializers.ImageField(source='profile.avatar', required=False)
    language = serializers.CharField(source='profile.language', required=False)
    timezone = serializers.CharField(source='profile.timezone', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
                 'position', 'department', 'bio', 'date_of_birth', 'avatar',
                 'language', 'timezone')
        read_only_fields = ('id', 'username')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        # Обновляем данные пользователя
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем данные профиля
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для входа в систему.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            raise serializers.ValidationError("Неверные учетные данные")
        if not user.is_active:
            raise serializers.ValidationError("Пользователь неактивен")
        data['user'] = user
        return data


class RegisterSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации.
    """
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Пароли не совпадают"
            })

        # Проверяем надежность пароля
        is_valid, error_message = validate_user_password(data['password'])
        if not is_valid:
            raise serializers.ValidationError({
                'password': error_message
            })

        # Проверяем уникальность username и email
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': "Пользователь с таким именем уже существует"
            })
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': "Пользователь с таким email уже существует"
            })

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сессий пользователя.
    """
    class Meta:
        model = UserSession
        fields = ('id', 'session_key', 'ip_address', 'user_agent', 'device_type', 'location',
                 'started_at', 'last_activity', 'ended_at')
        read_only_fields = fields


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для активности пользователя.
    """
    class Meta:
        model = UserActivity
        fields = ('id', 'activity_type', 'description', 'timestamp', 'ip_address',
                 'object_type', 'object_id')
        read_only_fields = fields 
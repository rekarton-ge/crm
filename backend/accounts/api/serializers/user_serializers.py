from django.contrib.auth import get_user_model
from rest_framework import serializers
from accounts.models import Role

User = get_user_model()


class RoleMinSerializer(serializers.ModelSerializer):
    """
    Минимальная сериализация роли для отображения в списке ролей пользователя.
    """

    class Meta:
        model = Role
        fields = ['id', 'name']


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения пользователя в списках.
    """
    roles = RoleMinSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_active', 'roles'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального отображения пользователя.
    """
    roles = RoleMinSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_joined', 'last_login', 'is_active',
            'is_staff', 'roles'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    roles = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 'is_active',
            'is_staff', 'roles'
        ]

    def validate(self, data):
        """
        Проверяет, что пароли совпадают.
        """
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        """
        Создает нового пользователя с зашифрованным паролем и назначенными ролями.
        """
        roles = validated_data.pop('roles', [])
        validated_data.pop('confirm_password', None)

        user = User.objects.create_user(**validated_data)

        # Назначаем роли
        if roles:
            from accounts.services.permission_service import PermissionService
            for role in roles:
                PermissionService.assign_role_to_user(user, role)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления данных пользователя (без пароля).
    """

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'is_active', 'is_staff'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля.
    """
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        """
        Проверяет, что старый пароль верный.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль введен неверно.")
        return value

    def validate(self, data):
        """
        Проверяет, что новые пароли совпадают.
        """
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Пароли не совпадают."})
        return data


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователя.
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})


class TokenRefreshSerializer(serializers.Serializer):
    """
    Сериализатор для обновления токена доступа.
    """
    refresh_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса сброса пароля.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля.
    """
    token = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    confirm_password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        """
        Проверяет, что пароли совпадают.
        """
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Пароли не совпадают."})
        return data
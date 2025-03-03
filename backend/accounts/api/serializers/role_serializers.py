from rest_framework import serializers
from accounts.models import Role, RoleAssignment, CustomPermission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения разрешений.
    """
    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomPermission
        fields = [
            'id', 'codename', 'name', 'description',
            'content_type', 'content_type_name', 'is_custom'
        ]

    def get_content_type_name(self, obj):
        """
        Возвращает читаемое имя типа контента.
        """
        if obj.content_type:
            return f"{obj.content_type.app_label}.{obj.content_type.model}"
        return None


class RoleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения ролей с разрешениями.
    """
    permissions = PermissionSerializer(many=True, read_only=True)
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'is_system',
            'permissions', 'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_system', 'created_at', 'updated_at']

    def get_user_count(self, obj):
        """
        Возвращает количество пользователей с данной ролью.
        """
        return obj.users.count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новой роли.
    """
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=CustomPermission.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']

    def validate_name(self, value):
        """
        Проверяет уникальность имени роли.
        """
        if Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Роль с таким именем уже существует.")
        return value

    def create(self, validated_data):
        """
        Создает новую роль с разрешениями.
        """
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)

        if permissions:
            role.permissions.set(permissions)

        return role


class RoleUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления роли.
    """
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=CustomPermission.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']

    def validate_name(self, value):
        """
        Проверяет уникальность имени роли.
        """
        # Если имя изменилось, проверяем его уникальность
        if self.instance and self.instance.name != value:
            if Role.objects.filter(name=value).exists():
                raise serializers.ValidationError("Роль с таким именем уже существует.")
        return value

    def validate(self, data):
        """
        Проверяет, что системная роль не изменяется.
        """
        if self.instance and self.instance.is_system:
            # Разрешаем изменять только описание системной роли
            if 'name' in data and data['name'] != self.instance.name:
                raise serializers.ValidationError(
                    {"name": "Нельзя изменять имя системной роли."}
                )

        return data

    def update(self, instance, validated_data):
        """
        Обновляет роль и ее разрешения.
        """
        permissions = validated_data.pop('permissions', None)

        # Обновляем обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Обновляем разрешения, если они были переданы
        if permissions is not None:
            instance.permissions.set(permissions)

        return instance


class RoleAssignmentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для назначения роли пользователю.
    """
    role_name = serializers.ReadOnlyField(source='role.name')
    assigned_by_username = serializers.ReadOnlyField(source='assigned_by.username')

    class Meta:
        model = RoleAssignment
        fields = [
            'id', 'user', 'role', 'role_name',
            'assigned_by', 'assigned_by_username',
            'assigned_at', 'expires_at'
        ]
        read_only_fields = ['id', 'assigned_at']

    def validate(self, data):
        """
        Проверяет, что роль не назначена пользователю ранее.
        """
        user = data.get('user')
        role = data.get('role')

        # Исключаем текущее назначение при обновлении
        if self.instance:
            if (self.instance.user == user and self.instance.role == role):
                return data

        # Проверяем существующие назначения
        if RoleAssignment.objects.filter(user=user, role=role).exists():
            raise serializers.ValidationError(
                {"role": f"Роль '{role.name}' уже назначена этому пользователю."}
            )

        return data
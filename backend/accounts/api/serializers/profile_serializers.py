from rest_framework import serializers
from accounts.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя.
    """
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user_id', 'avatar', 'avatar_url', 'position', 'department',
            'bio', 'date_of_birth', 'ui_settings', 'notification_settings',
            'language', 'timezone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']

    def get_avatar_url(self, obj):
        """
        Возвращает URL аватара пользователя, если он есть.
        """
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя.
    """

    class Meta:
        model = Profile
        fields = [
            'position', 'department', 'bio', 'date_of_birth',
            'language', 'timezone', 'ui_settings', 'notification_settings'
        ]

    def validate_ui_settings(self, value):
        """
        Проверяет корректность настроек интерфейса.
        """
        # Проверяем наличие обязательных полей
        required_keys = ['theme', 'dashboard_layout']
        for key in required_keys:
            if key not in value:
                value[key] = self.instance.get_default_ui_settings()[key]

        # Проверяем допустимые значения для темы
        allowed_themes = ['light', 'dark', 'system']
        if value.get('theme') not in allowed_themes:
            value['theme'] = 'light'

        # Проверяем допустимые значения для макета дашборда
        allowed_layouts = ['default', 'compact', 'full']
        if value.get('dashboard_layout') not in allowed_layouts:
            value['dashboard_layout'] = 'default'

        return value

    def validate_notification_settings(self, value):
        """
        Проверяет корректность настроек уведомлений.
        """
        # Проверяем наличие обязательных полей
        required_keys = ['email', 'web', 'push', 'digest']
        for key in required_keys:
            if key not in value:
                value[key] = self.instance.get_default_notification_settings()[key]

        # Проверяем, чтобы все значения были булевыми, кроме digest
        for key in ['email', 'web', 'push']:
            if not isinstance(value.get(key), bool):
                value[key] = True

        # Проверяем допустимые значения для дайджеста
        allowed_digest = ['none', 'daily', 'weekly', 'monthly']
        if value.get('digest') not in allowed_digest:
            value['digest'] = 'daily'

        return value


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления аватара пользователя.
    """

    class Meta:
        model = Profile
        fields = ['avatar']

    def validate_avatar(self, value):
        """
        Проверяет загруженный аватар (размер, формат).
        """
        if value:
            # Проверка размера файла (макс. 5 МБ)
            max_size = 5 * 1024 * 1024  # 5 МБ
            if value.size > max_size:
                raise serializers.ValidationError("Размер изображения не должен превышать 5 МБ.")

            # Проверка формата файла
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Недопустимый формат изображения. Разрешены форматы: JPEG, PNG, GIF."
                )

        return value
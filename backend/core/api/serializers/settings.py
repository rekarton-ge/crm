"""
Сериализаторы для работы с настройками системы.

Этот модуль предоставляет сериализаторы для API настроек системы,
позволяющие просматривать и изменять параметры конфигурации.
"""

from rest_framework import serializers

from core.api.serializers.base import BaseModelSerializer, DynamicFieldsModelSerializer
from core.models.settings import SystemSetting, UserSetting
from core.models.metadata import Setting


class SettingSerializer(BaseModelSerializer):
    """
    Сериализатор для модели настроек системы.

    Обеспечивает преобразование модели настроек в JSON и обратно,
    для работы с API настроек системы.
    """

    class Meta:
        """
        Метаданные сериализатора настроек.
        """
        model = Setting
        fields = ['id', 'key', 'value', 'description', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SettingCreateSerializer(BaseModelSerializer):
    """
    Сериализатор для создания настроек системы.

    Обеспечивает валидацию данных при создании новых настроек
    через API.
    """

    class Meta:
        """
        Метаданные сериализатора создания настроек.
        """
        model = Setting
        fields = ['key', 'value', 'description', 'is_public']

    def validate_key(self, value):
        """
        Проверяет уникальность ключа настройки.

        Args:
            value: Значение ключа для проверки.

        Returns:
            str: Проверенное значение ключа.

        Raises:
            serializers.ValidationError: Если ключ не уникален.
        """
        if Setting.objects.filter(key=value).exists():
            raise serializers.ValidationError("Настройка с таким ключом уже существует.")
        return value


class SettingUpdateSerializer(BaseModelSerializer):
    """
    Сериализатор для обновления настроек системы.

    Обеспечивает валидацию данных при обновлении существующих настроек
    через API.
    """

    class Meta:
        """
        Метаданные сериализатора обновления настроек.
        """
        model = Setting
        fields = ['value', 'description', 'is_public']


class SettingBulkUpdateSerializer(serializers.Serializer):
    """
    Сериализатор для массового обновления настроек.

    Позволяет обновлять несколько настроек за один запрос.
    """

    settings = serializers.ListField(
        child=serializers.DictField(),
        help_text="Список настроек для обновления",
        min_length=1
    )

    def validate_settings(self, value):
        """
        Проверяет корректность данных для массового обновления.

        Args:
            value: Список настроек для проверки.

        Returns:
            list: Проверенный список настроек.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        valid_settings = []
        errors = {}

        for i, setting_data in enumerate(value):
            if 'key' not in setting_data and 'id' not in setting_data:
                errors[i] = {"error": "Необходимо указать 'key' или 'id' настройки."}
                continue

            if 'value' not in setting_data:
                errors[i] = {"error": "Необходимо указать 'value' настройки."}
                continue

            # Проверяем существование настройки
            try:
                if 'id' in setting_data:
                    setting = Setting.objects.get(id=setting_data['id'])
                else:
                    setting = Setting.objects.get(key=setting_data['key'])

                # Добавляем id настройки для упрощения обновления
                setting_data['id'] = setting.id
                valid_settings.append(setting_data)
            except Setting.DoesNotExist:
                errors[i] = {"error": "Настройка не найдена."}

        if errors:
            raise serializers.ValidationError(errors)

        return valid_settings

    def update(self, instance, validated_data):
        """
        Обновляет настройки в соответствии с валидированными данными.

        Args:
            instance: Не используется в данном сериализаторе.
            validated_data: Валидированные данные для обновления настроек.

        Returns:
            list: Список обновленных настроек.
        """
        settings_data = validated_data.get('settings', [])
        updated_settings = []

        for setting_data in settings_data:
            setting = Setting.objects.get(id=setting_data['id'])

            # Обновляем только переданные поля
            if 'value' in setting_data:
                setting.value = setting_data['value']
            if 'description' in setting_data:
                setting.description = setting_data['description']
            if 'is_public' in setting_data:
                setting.is_public = setting_data['is_public']

            setting.save()
            updated_settings.append(setting)

        return updated_settings


class SettingCategorySerializer(serializers.Serializer):
    """
    Сериализатор для категорий настроек.

    Представляет сгруппированные по категориям настройки системы.
    """

    category = serializers.CharField()
    settings = SettingSerializer(many=True)


class SettingListByCategorySerializer(serializers.Serializer):
    """
    Сериализатор для вывода настроек, сгруппированных по категориям.

    Представляет список категорий настроек с настройками внутри каждой категории.
    """

    categories = SettingCategorySerializer(many=True)
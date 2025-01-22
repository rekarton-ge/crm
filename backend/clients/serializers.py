from rest_framework import serializers
from .models import Client, ClientGroup, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""
    class Meta:
        model = Tag
        fields = '__all__'


class ClientGroupSerializer(serializers.ModelSerializer):
    """Сериализатор для групп клиентов"""
    class Meta:
        model = ClientGroup
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    """Сериализатор для клиентов с группами и тегами"""
    group = ClientGroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(queryset=ClientGroup.objects.all(), source="group", write_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), source="tags", write_only=True, many=True)

    class Meta:
        model = Client
        fields = [
            "id", "client_type", "name", "email", "phone", "company",
            "legal_address", "fact_address", "inn", "kpp", "ogrn",
            "account_number", "correspondent_account", "bik", "bank_name",
            "director_full_name", "director_position", "director_basis",
            "signatory_full_name", "signatory_position", "signatory_basis",
            "contact_person", "contact_name", "contact_phone",
            "group", "group_id", "tags", "tag_ids", "created_at"
        ]
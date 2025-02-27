from rest_framework import serializers
from .models import Unit, Category, Product, PriceHistory


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name']


class PriceHistorySerializer(serializers.ModelSerializer):
    change_date_formatted = serializers.SerializerMethodField()

    class Meta:
        model = PriceHistory
        fields = ['id', 'old_price', 'new_price', 'change_date', 'change_date_formatted']

    def get_change_date_formatted(self, obj):
        return obj.change_date.strftime('%d.%m.%Y %H:%M')


class ProductSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_short_name = serializers.CharField(source='unit.short_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_history = PriceHistorySerializer(many=True, read_only=True)
    vat_display = serializers.CharField(source='get_vat_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'unit', 'unit_name', 'unit_short_name',
            'quantity', 'category', 'category_name',
            'purchase_price', 'selling_price', 'vat', 'vat_display',
            'created_at', 'updated_at', 'price_history'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'unit', 'quantity', 'category',
            'purchase_price', 'selling_price', 'vat'
        ]
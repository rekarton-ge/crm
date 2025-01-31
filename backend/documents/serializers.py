from rest_framework import serializers
from .models import Contract, Specification, Invoice, UPD
from clients.models import Client  # Импортируем модель Client
from clients.serializers import ClientSerializer  # Импортируем сериализатор Client из приложения clients


class ContractSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)  # Отображаем имя клиента
    files = serializers.SerializerMethodField()  # ✅ Добавляем файлы

    class Meta:
        model = Contract
        fields = ['id', 'number', 'name', 'date', 'client', 'client_name', 'status', 'igk_number', 'file', 'change_history', 'files']

    def get_files(self, obj):
        """Метод для получения прикрепленных файлов"""
        if hasattr(obj, 'files'):
            return [{'name': file.file.name, 'url': file.file.url} for file in obj.files.all()]
        return []


class SpecificationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    contract_number = serializers.CharField(source='contract.number', read_only=True)

    class Meta:
        model = Specification
        fields = ['id', 'number', 'date', 'client', 'client_name', 'contract', 'contract_number', 'igk_number', 'goods_services', 'total_amount', 'file', 'change_history']


class InvoiceSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Invoice (счет на оплату)"""
    client = ClientSerializer(read_only=True)  # Используем сериализатор из приложения clients
    contract = ContractSerializer(read_only=True)  # Вложенный сериализатор для договора
    specification = SpecificationSerializer(read_only=True)  # Вложенный сериализатор для спецификации

    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'date', 'client', 'contract', 'specification', 'status', 'payment_due_date',
            'goods_services', 'total_amount', 'comment', 'file', 'change_history'
        ]


class UPDSerializer(serializers.ModelSerializer):
    """Сериализатор для модели UPD (УПД)"""
    client = ClientSerializer(read_only=True)  # Используем сериализатор из приложения clients
    contract = ContractSerializer(read_only=True)  # Вложенный сериализатор для договора
    specification = SpecificationSerializer(read_only=True)  # Вложенный сериализатор для спецификации
    invoice = InvoiceSerializer(read_only=True)  # Вложенный сериализатор для счета на оплату

    class Meta:
        model = UPD
        fields = [
            'id', 'number', 'date', 'client', 'contract', 'specification', 'invoice', 'status', 'igk_number',
            'goods_services', 'total_amount', 'signing_status', 'file', 'change_history'
        ]
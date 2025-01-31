from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets
from .models import Contract, Specification, Invoice, UPD
from .serializers import ContractSerializer, SpecificationSerializer, InvoiceSerializer, UPDSerializer
from django.shortcuts import get_object_or_404  # ✅ Добавляем для проверки существования договора
from rest_framework.response import Response  # ✅ Добавляем Response для обработки ошибок


# ================================================================
# Contract (Договор)
# ================================================================

class ContractListCreateView(generics.ListCreateAPIView):
    """Список и создание договоров"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'status']
    search_fields = ['number', 'name']

    def get_queryset(self):
        """Отладка: Вывод всех договоров"""
        queryset = Contract.objects.all()
        print(f"🔍 Всего договоров в БД: {queryset.count()}")
        return queryset


class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление договора"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    def get_object(self):
        """Добавляем обработку ошибок, если договор не найден"""
        contract_id = self.kwargs.get("pk")
        print(f"🔎 Запрос на получение договора ID={contract_id}")

        contract = get_object_or_404(Contract, pk=contract_id)
        print(f"✅ Найден договор: {contract.number} - {contract.name}")

        return contract

    def retrieve(self, request, *args, **kwargs):
        """Переопределяем метод, чтобы явно обрабатывать ошибки"""
        try:
            contract = self.get_object()
            serializer = self.get_serializer(contract)
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Ошибка при получении договора: {str(e)}")
            return Response({"error": "Договор не найден"}, status=status.HTTP_404_NOT_FOUND)

# ================================================================
# Specification (Спецификация)
# ================================================================

class SpecificationListCreateView(generics.ListCreateAPIView):
    """Список и создание спецификаций"""
    queryset = Specification.objects.all()
    serializer_class = SpecificationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['contract', 'client']  # Фильтрация по договору и клиенту
    search_fields = ['number']  # Поиск по номеру спецификации


class SpecificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление спецификации"""
    queryset = Specification.objects.all()
    serializer_class = SpecificationSerializer


# ================================================================
# Invoice (Счет на оплату)
# ================================================================

class InvoiceListCreateView(generics.ListCreateAPIView):
    """Список и создание счетов"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['contract', 'specification', 'status']  # Фильтрация по договору, спецификации и статусу
    search_fields = ['number']  # Поиск по номеру счета


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление счета"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer


# ================================================================
# UPD (УПД)
# ================================================================

class UPDListCreateView(generics.ListCreateAPIView):
    """Список и создание УПД"""
    queryset = UPD.objects.all()
    serializer_class = UPDSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['contract', 'specification', 'invoice', 'status']  # Фильтрация по договору, спецификации, счету и статусу
    search_fields = ['number']  # Поиск по номеру УПД


class UPDDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление УПД"""
    queryset = UPD.objects.all()
    serializer_class = UPDSerializer


# ================================================================
# Дополнительные представления
# ================================================================

class ContractSpecificationsView(generics.ListAPIView):
    """Список спецификаций для конкретного договора"""
    serializer_class = SpecificationSerializer

    def get_queryset(self):
        contract_id = self.kwargs['contract_id']
        return Specification.objects.filter(contract_id=contract_id)


class SpecificationInvoicesView(generics.ListAPIView):
    """Список счетов для конкретной спецификации"""
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        specification_id = self.kwargs['specification_id']
        return Invoice.objects.filter(specification_id=specification_id)

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    parser_classes = (MultiPartParser, FormParser)  # ✅ Добавлено для загрузки файлов
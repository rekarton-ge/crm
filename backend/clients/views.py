import django_filters
from io import BytesIO
import pandas as pd
from django.http import HttpResponse
from django.contrib.postgres.search import SearchVector, SearchQuery
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from openpyxl import Workbook
from .models import Client, ClientGroup, Tag
from .serializers import ClientSerializer, ClientGroupSerializer, TagSerializer
from django.db.models import Q
from .services import check_contractor


# Фильтр для клиентов
class ClientFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(), conjoined=False)
    company = django_filters.CharFilter(lookup_expr="icontains")
    inn = django_filters.CharFilter(lookup_expr="iexact")
    created_at = django_filters.DateFromToRangeFilter()
    client_type = django_filters.ChoiceFilter(choices=Client.CLIENT_TYPE_CHOICES)

    class Meta:
        model = Client
        fields = ["client_type", "company", "group", "tags", "created_at", "inn"]


# API для управления клиентами
class ClientViewSet(viewsets.ModelViewSet):
    """API для управления клиентами"""
    queryset = Client.objects.prefetch_related("tags").select_related("group")
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ClientFilter
    search_fields = ["name", "company", "email", "phone", "inn"]  # Только нужные поля

    def get_queryset(self):
        """Гибридный поиск: полнотекстовый по name и company, обычный по phone, email, inn."""
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "").strip()

        if search_query:
            # Полнотекстовый поиск по name и company
            search_vector = SearchVector("name", "company", config="russian")
            search_query_obj = SearchQuery(search_query, config="russian")

            # Обычный поиск по phone, email, inn
            queryset = queryset.annotate(
                search=search_vector
            ).filter(
                Q(search=search_query_obj) |  # Полнотекстовый поиск
                Q(phone__icontains=search_query) |  # Поиск по телефону
                Q(email__icontains=search_query) |  # Поиск по email
                Q(inn__icontains=search_query)  # Поиск по ИНН
            )

        return queryset

    @action(detail=False, methods=["get"], url_path="export", url_name="export_clients")
    def export_clients(self, request, *args, **kwargs):
        """Экспорт клиентов в CSV/Excel."""
        file_format = request.GET.get("file_format", "csv").lower()
        clients = Client.objects.all().values(
            "id", "client_type", "name", "email", "phone", "company",
            "legal_address", "fact_address", "inn", "created_at"
        )

        if not clients.exists():
            return Response({"error": "Нет данных для экспорта"}, status=400)

        df = pd.DataFrame(clients)

        if "created_at" in df.columns and not df["created_at"].isnull().all():
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

        if file_format == "xlsx":
            output = BytesIO()
            wb = Workbook()
            ws = wb.active
            ws.append(df.columns.tolist())

            for row in df.itertuples(index=False, name=None):
                ws.append(row)

            wb.save(output)
            output.seek(0)

            response = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="clients.xlsx"'
            return response

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="clients.csv"'
        df.to_csv(response, index=False)
        return response

    @action(detail=False, methods=["get"], url_path="find-duplicates")
    def find_duplicates(self, request):
        """Поиск дубликатов клиентов."""
        duplicates = []
        clients = Client.objects.all()
        for client in clients:
            matches = Client.objects.filter(
                Q(phone=client.phone) | Q(email=client.email) | Q(inn=client.inn)
            ).exclude(id=client.id)
            if matches.exists():
                duplicates.append({"client": client, "matches": matches})
        return Response(duplicates)

    @action(detail=True, methods=["get"], url_path="check-contractor")
    def check_contractor(self, request, pk=None):
        """Проверка контрагента по ИНН."""
        client = self.get_object()  # Использует pk для поиска клиента
        if not client.inn:
            return Response({"error": "ИНН не указан"}, status=400)

        result = check_contractor(client.inn)
        if result:
            return Response(result)
        return Response({"error": "Не удалось проверить контрагента"}, status=500)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        """Массовое удаление клиентов."""
        ids = request.data.get("ids", [])
        Client.objects.filter(id__in=ids).delete()
        return Response({"status": "success"})

    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request):
        """Массовое редактирование клиентов."""
        ids = request.data.get("ids", [])
        updates = request.data.get("updates", {})
        Client.objects.filter(id__in=ids).update(**updates)
        return Response({"status": "success"})


# API для управления группами клиентов
class ClientGroupViewSet(viewsets.ModelViewSet):
    """API для управления группами клиентов"""
    queryset = ClientGroup.objects.all()
    serializer_class = ClientGroupSerializer


# API для управления тегами клиентов
class TagViewSet(viewsets.ModelViewSet):
    """API для управления тегами клиентов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
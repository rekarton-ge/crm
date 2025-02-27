from django.urls import path
from . import views
from .views_pdf_extractor import ExtractPDFDataView

urlpatterns = [
    # Contract (Договор)
    path('contracts/', views.ContractListCreateView.as_view(), name='contract-list-create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),

    # Specification (Спецификация)
    path('specifications/', views.SpecificationListCreateView.as_view(), name='specification-list-create'),
    path('specifications/<int:pk>/', views.SpecificationDetailView.as_view(), name='specification-detail'),

    # Invoice (Счет на оплату)
    path('invoices/', views.InvoiceListCreateView.as_view(), name='invoice-list-create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),

    # UPD (УПД)
    path('upds/', views.UPDListCreateView.as_view(), name='upd-list-create'),
    path('upds/<int:pk>/', views.UPDDetailView.as_view(), name='upd-detail'),

    # Дополнительные представления
    path('contracts/<int:contract_id>/specifications/', views.ContractSpecificationsView.as_view(), name='contract-specifications'),
    path('specifications/<int:specification_id>/invoices/', views.SpecificationInvoicesView.as_view(), name='specification-invoices'),
    path('extract-pdf-data/', ExtractPDFDataView.as_view(), name='extract-pdf-data'),
]
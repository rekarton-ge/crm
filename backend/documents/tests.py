import json
from django.test import TestCase, Client as DjangoTestClient
from django.urls import reverse
from rest_framework import status
from .models import Contract, Specification, Invoice, UPD
from clients.models import Client

class ContractTests(TestCase):
    def setUp(self):
        # Очищаем базу данных перед каждым тестом
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

        # Создаем тестовые данные
        self.client = DjangoTestClient()
        self.client_obj = Client.objects.create(name='Test Client', email='client@test.com', phone='1234567890')
        self.contract_data = {
            'number': 'CONTRACT-001',
            'name': 'Test Contract',
            'date': '2023-10-01',
            'client': self.client_obj,
            'status': 'Подписан',
            'igk_number': 'IGK-001',
            'file': 'contracts/contract.pdf'
        }
        self.contract = Contract.objects.create(**self.contract_data)

    def tearDown(self):
        # Очищаем базу данных после каждого теста
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

    def test_contract_creation(self):
        self.assertEqual(self.contract.number, 'CONTRACT-001')
        self.assertEqual(self.contract.name, 'Test Contract')
        self.assertEqual(self.contract.status, 'Подписан')

    def test_contract_list_view(self):
        response = self.client.get(reverse('contract-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Ожидаем только один объект

    def test_contract_detail_view(self):
        response = self.client.get(reverse('contract-detail', kwargs={'pk': self.contract.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 'CONTRACT-001')

class SpecificationTests(TestCase):
    def setUp(self):
        # Очищаем базу данных перед каждым тестом
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

        # Создаем тестовые данные
        self.client = DjangoTestClient()
        self.client_obj = Client.objects.create(name='Test Client', email='client@test.com', phone='1234567890')
        self.contract = Contract.objects.create(
            number='CONTRACT-001',
            name='Test Contract',
            date='2023-10-01',
            client=self.client_obj,
            status='Подписан',
            igk_number='IGK-001',
            file='contracts/contract.pdf'
        )
        self.specification_data = {
            'number': 1,
            'date': '2023-10-01',
            'client': self.client_obj,
            'contract': self.contract,
            'igk_number': 'IGK-001',
            'goods_services': 'Test goods/services',
            'total_amount': 1000.00,
            'file': 'specifications/specification.pdf'
        }
        self.specification = Specification.objects.create(**self.specification_data)

    def tearDown(self):
        # Очищаем базу данных после каждого теста
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

    def test_specification_creation(self):
        self.assertEqual(self.specification.number, 1)
        self.assertEqual(self.specification.goods_services, 'Test goods/services')
        self.assertEqual(self.specification.total_amount, 1000.00)

    def test_specification_list_view(self):
        response = self.client.get(reverse('specification-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Ожидаем только один объект

    def test_specification_detail_view(self):
        response = self.client.get(reverse('specification-detail', kwargs={'pk': self.specification.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 1)

class InvoiceTests(TestCase):
    def setUp(self):
        # Очищаем базу данных перед каждым тестом
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

        # Создаем тестовые данные
        self.client = DjangoTestClient()
        self.client_obj = Client.objects.create(name='Test Client', email='client@test.com', phone='1234567890')
        self.contract = Contract.objects.create(
            number='CONTRACT-001',
            name='Test Contract',
            date='2023-10-01',
            client=self.client_obj,
            status='Подписан',
            igk_number='IGK-001',
            file='contracts/contract.pdf'
        )
        self.specification = Specification.objects.create(
            number=1,
            date='2023-10-01',
            client=self.client_obj,
            contract=self.contract,
            igk_number='IGK-001',
            goods_services='Test goods/services',
            total_amount=1000.00,
            file='specifications/specification.pdf'
        )
        self.invoice_data = {
            'number': 'INVOICE-001',
            'date': '2023-10-01',
            'client': self.client_obj,
            'contract': self.contract,
            'specification': self.specification,
            'status': 'Оплачен',
            'payment_due_date': '2023-10-15',
            'goods_services': 'Test goods/services',
            'total_amount': 1000.00,
            'comment': 'Test comment',
            'file': 'invoices/invoice.pdf'
        }
        self.invoice = Invoice.objects.create(**self.invoice_data)

    def tearDown(self):
        # Очищаем базу данных после каждого теста
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

    def test_invoice_creation(self):
        self.assertEqual(self.invoice.number, 'INVOICE-001')
        self.assertEqual(self.invoice.status, 'Оплачен')
        self.assertEqual(self.invoice.total_amount, 1000.00)

    def test_invoice_list_view(self):
        response = self.client.get(reverse('invoice-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Ожидаем только один объект

    def test_invoice_detail_view(self):
        response = self.client.get(reverse('invoice-detail', kwargs={'pk': self.invoice.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 'INVOICE-001')

class UPDTests(TestCase):
    def setUp(self):
        # Очищаем базу данных перед каждым тестом
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

        # Создаем тестовые данные
        self.client = DjangoTestClient()
        self.client_obj = Client.objects.create(name='Test Client', email='client@test.com', phone='1234567890')
        self.contract = Contract.objects.create(
            number='CONTRACT-001',
            name='Test Contract',
            date='2023-10-01',
            client=self.client_obj,
            status='Подписан',
            igk_number='IGK-001',
            file='contracts/contract.pdf'
        )
        self.specification = Specification.objects.create(
            number=1,
            date='2023-10-01',
            client=self.client_obj,
            contract=self.contract,
            igk_number='IGK-001',
            goods_services='Test goods/services',
            total_amount=1000.00,
            file='specifications/specification.pdf'
        )
        self.invoice = Invoice.objects.create(
            number='INVOICE-001',
            date='2023-10-01',
            client=self.client_obj,
            contract=self.contract,
            specification=self.specification,
            status='Оплачен',
            payment_due_date='2023-10-15',
            goods_services='Test goods/services',
            total_amount=1000.00,
            comment='Test comment',
            file='invoices/invoice.pdf'
        )
        self.upd_data = {
            'number': 'UPD-001',
            'date': '2023-10-01',
            'client': self.client_obj,
            'contract': self.contract,
            'specification': self.specification,
            'invoice': self.invoice,
            'status': 'Оплачен',
            'igk_number': 'IGK-001',
            'goods_services': 'Test goods/services',
            'total_amount': 1000.00,
            'signing_status': 'Подписан в оригинале',
            'file': 'upds/upd.pdf'
        }
        self.upd = UPD.objects.create(**self.upd_data)

    def tearDown(self):
        # Очищаем базу данных после каждого теста
        Contract.objects.all().delete()
        Specification.objects.all().delete()
        Invoice.objects.all().delete()
        UPD.objects.all().delete()

    def test_upd_creation(self):
        self.assertEqual(self.upd.number, 'UPD-001')
        self.assertEqual(self.upd.status, 'Оплачен')
        self.assertEqual(self.upd.total_amount, 1000.00)

    def test_upd_list_view(self):
        response = self.client.get(reverse('upd-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Ожидаем только один объект

    def test_upd_detail_view(self):
        response = self.client.get(reverse('upd-detail', kwargs={'pk': self.upd.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 'UPD-001')
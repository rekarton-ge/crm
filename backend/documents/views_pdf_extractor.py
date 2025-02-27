# backend/documents/views_pdf_extractor.py
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.db import models
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from clients.models import Client
from .models import Contract

# Подключаем библиотеку для работы с PDF
try:
    import PyPDF2
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2


class ExtractPDFDataView(APIView):
    """
    API-представление для извлечения данных из PDF-файла спецификации
    """
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        if 'file' not in request.FILES:
            return Response({'error': 'Файл не предоставлен'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = request.FILES['file']

        # Создаем временный файл для сохранения PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)

        try:
            # Извлекаем данные из PDF
            extracted_data = self.extract_data_from_pdf(temp_file_path)

            # Удаляем временный файл
            os.unlink(temp_file_path)

            return Response(extracted_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Удаляем временный файл в случае ошибки
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

            return Response({'error': f'Ошибка при извлечении данных: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_data_from_pdf(self, pdf_path):
        """
        Извлекает данные из PDF файла спецификации
        """
        extracted_data = {
            'number': None,
            'date': None,
            'client_id': None,
            'client_name': None,
            'contract_id': None,
            'contract_number': None,
            'total_amount': None
        }

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # Извлекаем текст из первой страницы, где обычно находятся основные данные
            text = ""
            for page_num in range(min(3, len(reader.pages))):  # Проверяем первые 3 страницы
                text += reader.pages[page_num].extract_text()

            # Извлекаем номер спецификации
            number_match = re.search(r'Спецификация\s+№\s*(\d+)', text, re.IGNORECASE) or \
                           re.search(r'№\s*(\d+)', text)
            if number_match:
                extracted_data['number'] = number_match.group(1).strip()

            # Извлекаем дату
            date_match = re.search(r'от\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', text) or \
                         re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', text)
            if date_match:
                date_str = date_match.group(1)
                try:
                    # Пытаемся распознать формат даты
                    if '.' in date_str:
                        day, month, year = map(int, date_str.split('.'))
                    elif '/' in date_str:
                        day, month, year = map(int, date_str.split('/'))
                    elif '-' in date_str:
                        day, month, year = map(int, date_str.split('-'))
                    else:
                        day, month, year = None, None, None

                    if day and month and year:
                        # Корректируем год, если он двузначный
                        if year < 100:
                            year += 2000

                        extracted_data['date'] = f"{year}-{month:02d}-{day:02d}"
                except Exception:
                    # Если не получилось распознать дату, оставляем None
                    pass

            # Извлекаем название клиента
            client_match = re.search(r'(?:Заказчик|Покупатель|Клиент):\s*([^\n,]*)', text, re.IGNORECASE)
            if client_match:
                client_name = client_match.group(1).strip()
                extracted_data['client_name'] = client_name

                # Ищем клиента в базе данных по имени
                try:
                    client = Client.objects.filter(
                        models.Q(name__icontains=client_name) |
                        models.Q(company__icontains=client_name)
                    ).first()

                    if client:
                        extracted_data['client_id'] = client.id
                except Exception:
                    pass

            # Извлекаем номер договора
            contract_match = re.search(r'(?:Договор|Контракт)\s+№\s*([^\n,]*)', text, re.IGNORECASE)
            if contract_match:
                contract_number = contract_match.group(1).strip()
                extracted_data['contract_number'] = contract_number

                # Если нашли клиента, ищем договор по номеру и клиенту
                if extracted_data['client_id']:
                    try:
                        contract = Contract.objects.filter(
                            number__icontains=contract_number,
                            client_id=extracted_data['client_id']
                        ).first()

                        if contract:
                            extracted_data['contract_id'] = contract.id
                    except Exception:
                        pass
                else:
                    # Если клиент не найден, просто ищем по номеру договора
                    try:
                        contract = Contract.objects.filter(
                            number__icontains=contract_number
                        ).first()

                        if contract:
                            extracted_data['contract_id'] = contract.id
                            # Если нашли договор, но не нашли клиента, берем клиента из договора
                            extracted_data['client_id'] = contract.client_id
                    except Exception:
                        pass

            # Извлекаем общую сумму
            amount_match = re.search(r'(?:Общая сумма|Итого|Всего)[\s:]*(\d[\d\s.,]*)', text, re.IGNORECASE)
            if amount_match:
                amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
                try:
                    # Удаляем все символы, кроме цифр и точки
                    amount_clean = re.sub(r'[^\d.]', '', amount_str)
                    extracted_data['total_amount'] = float(amount_clean)
                except Exception:
                    pass

        return extracted_data
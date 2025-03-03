"""
Представления для работы с файлами.

Этот модуль содержит представления для загрузки и управления файлами.
"""

from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import magic

class FileUploadViewSet(viewsets.ViewSet):
    """
    Представление для загрузки файлов.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    # Разрешенные типы файлов
    ALLOWED_MIME_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    # Максимальный размер файла (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    def create(self, request):
        """
        Загрузка файла.
        """
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response(
                {'error': 'Файл не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка размера файла
        if file_obj.size > self.MAX_FILE_SIZE:
            return Response(
                {'error': 'Размер файла превышает допустимый лимит'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка типа файла
        mime = magic.from_buffer(file_obj.read(1024), mime=True)
        file_obj.seek(0)  # Сброс указателя чтения
        
        if mime not in self.ALLOWED_MIME_TYPES:
            return Response(
                {'error': 'Недопустимый тип файла'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Сохранение файла
        try:
            upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, file_obj.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            return Response(
                {'message': 'Файл успешно загружен'},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
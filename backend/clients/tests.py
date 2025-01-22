from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Client, ClientGroup, Tag
from .serializers import ClientSerializer, ClientGroupSerializer, TagSerializer


class ModelTests(TestCase):
    def setUp(self):
        """Создаём тестовые данные."""
        self.group = ClientGroup.objects.create(name="Группа 1")
        self.tag = Tag.objects.create(name="Тег 1")
        self.client = Client.objects.create(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+79991234567",
            group=self.group,
        )
        self.client.tags.add(self.tag)

    def test_client_creation(self):
        """Проверяем, что клиент создаётся корректно."""
        self.assertEqual(self.client.name, "Иван Иванов")
        self.assertEqual(self.client.email, "ivan@example.com")
        self.assertEqual(self.client.phone, "+79991234567")
        self.assertEqual(self.client.group.name, "Группа 1")
        self.assertEqual(self.client.tags.first().name, "Тег 1")

    def test_client_str(self):
        """Проверяем строковое представление клиента."""
        self.assertEqual(str(self.client), "Иван Иванов")

    def test_group_str(self):
        """Проверяем строковое представление группы."""
        self.assertEqual(str(self.group), "Группа 1")

    def test_tag_str(self):
        """Проверяем строковое представление тега."""
        self.assertEqual(str(self.tag), "Тег 1")


class SerializerTests(TestCase):
    def setUp(self):
        """Создаём тестовые данные."""
        self.group = ClientGroup.objects.create(name="Группа 1")
        self.tag = Tag.objects.create(name="Тег 1")
        self.client = Client.objects.create(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+79991234567",
            group=self.group,
        )
        self.client.tags.add(self.tag)

    def test_client_serializer(self):
        """Проверяем сериализатор клиента."""
        serializer = ClientSerializer(self.client)
        self.assertEqual(serializer.data["name"], "Иван Иванов")
        self.assertEqual(serializer.data["email"], "ivan@example.com")
        self.assertEqual(serializer.data["phone"], "+79991234567")
        self.assertEqual(serializer.data["group"]["name"], "Группа 1")
        self.assertEqual(serializer.data["tags"][0]["name"], "Тег 1")

    def test_group_serializer(self):
        """Проверяем сериализатор группы."""
        serializer = ClientGroupSerializer(self.group)
        self.assertEqual(serializer.data["name"], "Группа 1")

    def test_tag_serializer(self):
        """Проверяем сериализатор тега."""
        serializer = TagSerializer(self.tag)
        self.assertEqual(serializer.data["name"], "Тег 1")


class APITests(TestCase):
    def setUp(self):
        """Создаём тестовые данные и клиент для API."""
        self.client_api = APIClient()
        self.group = ClientGroup.objects.create(name="Группа 1")
        self.tag = Tag.objects.create(name="Тег 1")
        self.client = Client.objects.create(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+79991234567",
            group=self.group,
        )
        self.client.tags.add(self.tag)

    def test_get_clients(self):
        """Проверяем получение списка клиентов."""
        url = reverse("clients-list")
        response = self.client_api.get(url)
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)

        # Учитываем пагинацию
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)  # Проверяем количество элементов
        self.assertEqual(response.data["results"], serializer.data)  # Проверяем данные

    def test_get_client_detail(self):
        """Проверяем получение деталей клиента."""
        url = reverse("clients-detail", args=[self.client.id])
        response = self.client_api.get(url)
        serializer = ClientSerializer(self.client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_client(self):
        """Проверяем создание нового клиента."""
        url = reverse("clients-list")
        data = {
            "name": "Петр Петров",
            "email": "petr@example.com",
            "phone": "+79997654321",
            "group_id": self.group.id,
            "tag_ids": [self.tag.id],
        }
        response = self.client_api.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 2)

        # Проверяем, что группа и теги корректно связаны с клиентом
        new_client = Client.objects.get(id=response.data["id"])
        self.assertEqual(new_client.group.id, self.group.id)
        self.assertEqual(new_client.tags.first().id, self.tag.id)

    def test_update_client(self):
        """Проверяем обновление клиента."""
        url = reverse("clients-detail", args=[self.client.id])
        data = {
            "name": "Иван Иванов (обновлённый)",
            "group_id": self.group.id,
            "tag_ids": [self.tag.id],
        }
        response = self.client_api.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.refresh_from_db()
        self.assertEqual(self.client.name, "Иван Иванов (обновлённый)")
        self.assertEqual(self.client.group.id, self.group.id)
        self.assertEqual(self.client.tags.first().id, self.tag.id)

    def test_delete_client(self):
        """Проверяем удаление клиента."""
        url = reverse("clients-detail", args=[self.client.id])
        response = self.client_api.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Client.objects.count(), 0)


class SignalTests(TestCase):
    def setUp(self):
        """Создаём тестовые данные."""
        self.client = Client.objects.create(
            name="Иван Иванов",
            email="ivan@example.com",
            phone="+79991234567",
        )

    def test_search_vector_update(self):
        """Проверяем, что search_vector обновляется после сохранения клиента."""
        self.client.name = "Иван Иванов (обновлённый)"
        self.client.save()
        self.client.refresh_from_db()
        self.assertIsNotNone(self.client.search_vector)

        # Проверяем, что search_vector содержит лексемы, связанные с обновлённым именем
        self.assertIn("иван", str(self.client.search_vector).lower())
        self.assertIn("обновлен", str(self.client.search_vector).lower())
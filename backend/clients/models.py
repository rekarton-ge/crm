from django.db import models
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.db.models import F
import phonenumbers
from phonenumbers import PhoneNumberFormat
from simple_history.models import HistoricalRecords


def normalize_phone(phone):
    """Приводит номер телефона к единому формату."""
    try:
        parsed = phonenumbers.parse(phone, "RU")  # Указываем страну (например, Россия)
        return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone  # Возвращаем исходный номер, если не удалось распарсить


class ClientGroup(models.Model):
    """Группы клиентов"""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа клиентов"
        verbose_name_plural = "Группы клиентов"


class Tag(models.Model):
    """Теги клиентов"""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Client(models.Model):
    """Модель клиента в CRM"""

    CLIENT_TYPE_CHOICES = [
        ("IP", "Индивидуальный предприниматель"),
        ("LEGAL", "Юридическое лицо"),
    ]

    client_type = models.CharField(
        max_length=10,
        choices=CLIENT_TYPE_CHOICES,
        default="LEGAL",
        verbose_name="Вид клиента",
    )
    name = models.CharField(max_length=255, verbose_name="Наименование клиента")
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name="Компания")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    inn = models.CharField(max_length=12, blank=True, null=True, verbose_name="ИНН")

    # Поле для полнотекстового поиска
    search_vector = SearchVectorField(null=True, blank=True)

    # Адреса
    legal_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Юридический адрес")
    fact_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фактический адрес")

    # Финансовая информация
    kpp = models.CharField(max_length=9, blank=True, null=True, verbose_name="КПП")  # Только для юр. лиц
    ogrn = models.CharField(max_length=15, blank=True, null=True, verbose_name="ОГРН")
    account_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Расчётный счёт")
    correspondent_account = models.CharField(max_length=20, blank=True, null=True, verbose_name="Корреспондентский счёт")
    bik = models.CharField(max_length=9, blank=True, null=True, verbose_name="БИК Банка")
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Наименование Банка")

    # Директор
    director_full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ФИО Директора")
    director_position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Должность Директора")
    director_basis = models.CharField(max_length=255, blank=True, null=True, verbose_name="Основание")

    # Подписант
    signatory_full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ФИО подписанта")
    signatory_position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Должность подписанта")
    signatory_basis = models.CharField(max_length=255, blank=True, null=True, verbose_name="Основание подписанта")

    # Контактное лицо
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Контактное лицо компании")
    contact_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя контактного лица")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон контактного лица")

    # Группа и теги
    group = models.ForeignKey(ClientGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")

    # Дата создания
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # История изменений
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация модели перед сохранением"""
        super().clean()

        if self.client_type == "IP":
            self.kpp = None  # КПП не должно заполняться для ИП
        if not self.fact_address and self.legal_address:
            self.fact_address = self.legal_address  # Автозаполнение фактического адреса

    def save(self, *args, **kwargs):
        """Нормализация номера телефона и обновление search_vector перед сохранением"""
        self.phone = normalize_phone(self.phone)  # Нормализуем номер телефона
        is_new = self.pk is None  # Проверяем, новый ли объект
        super().save(*args, **kwargs)  # Сначала сохраняем без SearchVector

        # Обновляем search_vector
        if not is_new:
            Client.objects.filter(pk=self.pk).update(
                search_vector=SearchVector(
                    F("name"), F("company"), F("phone"), F("email"), F("inn"),
                    config="russian"
                )
            )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["-created_at"]
        indexes = [
            GinIndex(fields=["search_vector"], name="client_search_vector_idx"),
        ]


class ClientRelationship(models.Model):
    """Связи между клиентами (филиалы, партнёры и т.д.)"""
    RELATIONSHIP_TYPES = [
        ("BRANCH", "Филиал"),
        ("PARTNER", "Партнёр"),
        ("PARENT", "Головная компания"),
    ]

    from_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="relationships_from")
    to_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="relationships_to")
    relationship_type = models.CharField(max_length=10, choices=RELATIONSHIP_TYPES)

    def __str__(self):
        return f"{self.from_client} -> {self.to_client} ({self.relationship_type})"

    class Meta:
        verbose_name = "Связь клиентов"
        verbose_name_plural = "Связи клиентов"
        indexes = [
            models.Index(fields=["from_client", "to_client"]),
        ]


class Interaction(models.Model):
    """Взаимодействия с клиентами (звонки, встречи, письма)"""
    INTERACTION_TYPES = [
        ("CALL", "Звонок"),
        ("MEETING", "Встреча"),
        ("EMAIL", "Письмо"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="interactions")
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} - {self.interaction_type} ({self.date})"

    class Meta:
        verbose_name = "Взаимодействие"
        verbose_name_plural = "Взаимодействия"
        indexes = [
            models.Index(fields=["client", "date"]),
        ]

#тест
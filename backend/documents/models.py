from django.db import models
from django.utils import timezone
from clients.models import Client  # Импортируем модель Client из приложения clients
import os

# Функция для генерации пути для файлов договора
def get_contract_upload_path(instance, filename):
    return f"docs/{instance.client.id}/contracts_{instance.number}/{filename}"

# Функция для генерации пути для файлов спецификации
def get_specification_upload_path(instance, filename):
    return f"docs/{instance.client.id}/contracts_{instance.contract.number}/specifications_{instance.number}/{filename}"

# Функция для генерации пути для файлов счета на оплату
def get_invoice_upload_path(instance, filename):
    if instance.contract:
        return f"docs/{instance.client.id}/contracts_{instance.contract.number}/invoice/{filename}"
    else:
        return f"docs/{instance.client.id}/invoice/{filename}"

# Функция для генерации пути для файлов УПД
def get_upd_upload_path(instance, filename):
    if instance.contract:
        return f"docs/{instance.client.id}/contracts_{instance.contract.number}/invoice/upd/{filename}"
    else:
        return f"docs/{instance.client.id}/invoice/upd/{filename}"

class Contract(models.Model):
    number = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Номер договора")
    name = models.CharField(max_length=255, verbose_name="Имя договора")
    date = models.DateField(default=timezone.now, verbose_name="Дата договора")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    status = models.CharField(
        max_length=50,
        choices=[("Подписан", "Подписан"), ("Не подписан", "Не подписан"), ("На согласовании", "На согласовании")],
        verbose_name="Статус"
    )
    igk_number = models.CharField(max_length=50, blank=True, verbose_name="Номер ИГК")
    file = models.FileField(upload_to=get_contract_upload_path, blank=True, null=True, verbose_name="Файл договора")
    change_history = models.JSONField(null=True, blank=True, verbose_name="История изменений")

    def save(self, *args, **kwargs):
        if not self.number:
            today = timezone.now().strftime('%d%m%y')
            last_contract = Contract.objects.filter(number__startswith=today).order_by('number').last()
            if last_contract:
                last_number = int(last_contract.number.split('-')[-1])
                self.number = f"{today}-{last_number + 1}"
            else:
                self.number = f"{today}-1"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} - {self.name}"

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"


class Specification(models.Model):
    number = models.IntegerField(verbose_name="Номер спецификации")
    date = models.DateField(default=timezone.now, verbose_name="Дата спецификации")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, verbose_name="Договор")
    igk_number = models.CharField(max_length=50, blank=True, verbose_name="Номер ИГК")
    goods_services = models.TextField(verbose_name="Товары/Услуги")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    file = models.FileField(upload_to=get_contract_upload_path, blank=True, null=True, verbose_name="Файл спецификации")
    change_history = models.JSONField(null=True, blank=True, verbose_name="История изменений")

    def save(self, *args, **kwargs):
        if not self.number:
            last_spec = Specification.objects.filter(contract=self.contract).order_by('number').last()
            if last_spec:
                self.number = last_spec.number + 1
            else:
                self.number = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Спецификация №{self.number} к договору {self.contract.number}"

    class Meta:
        verbose_name = "Спецификация"
        verbose_name_plural = "Спецификации"
        unique_together = ('contract', 'number')  # Уникальность номера спецификации в рамках контракта


class Invoice(models.Model):
    number = models.CharField(max_length=50, verbose_name="Номер счета")
    date = models.DateField(verbose_name="Дата счета")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Договор")
    specification = models.ForeignKey(Specification, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Спецификация")
    status = models.CharField(
        max_length=50,
        choices=[("Оплачен", "Оплачен"), ("Оплачен частично", "Оплачен частично"), ("Не оплачен", "Не оплачен"), ("Отменен", "Отменен")],
        verbose_name="Статус"
    )
    payment_due_date = models.DateField(verbose_name="Срок оплаты")
    goods_services = models.TextField(verbose_name="Товары/Услуги")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    file = models.FileField(upload_to=get_invoice_upload_path, blank=True, null=True, verbose_name="Файл счета")
    change_history = models.JSONField(null=True, blank=True, verbose_name="История изменений")

    def __str__(self):
        return f"Счет №{self.number} от {self.date}"

    class Meta:
        verbose_name = "Счет на оплату"
        verbose_name_plural = "Счета на оплату"


class UPD(models.Model):
    number = models.CharField(max_length=50, verbose_name="Номер УПД")
    date = models.DateField(verbose_name="Дата УПД")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Договор")
    specification = models.ForeignKey(Specification, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Спецификация")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Счет на оплату")
    status = models.CharField(
        max_length=50,
        choices=[("Оплачен", "Оплачен"), ("Оплачен частично", "Оплачен частично"), ("Не оплачен", "Не оплачен")],
        verbose_name="Статус"
    )
    igk_number = models.CharField(max_length=50, blank=True, verbose_name="Номер ИГК")
    goods_services = models.TextField(verbose_name="Товары/Услуги")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    signing_status = models.CharField(
        max_length=50,
        choices=[("Подписана по ЭДО", "Подписана по ЭДО"), ("Подписан в оригинале", "Подписан в оригинале"), ("Не подписан", "Не подписан")],
        verbose_name="Статус подписания"
    )
    file = models.FileField(upload_to=get_upd_upload_path, blank=True, null=True, verbose_name="Файл УПД")
    change_history = models.JSONField(null=True, blank=True, verbose_name="История изменений")

    def __str__(self):
        return f"УПД №{self.number} от {self.date}"

    class Meta:
        verbose_name = "УПД"
        verbose_name_plural = "УПД"
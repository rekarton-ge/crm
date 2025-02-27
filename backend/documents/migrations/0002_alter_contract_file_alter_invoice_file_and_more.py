# Generated by Django 5.1.5 on 2025-01-29 07:16

import documents.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=documents.models.get_contract_upload_path, verbose_name='Файл договора'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=documents.models.get_invoice_upload_path, verbose_name='Файл счета'),
        ),
        migrations.AlterField(
            model_name='specification',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=documents.models.get_contract_upload_path, verbose_name='Файл спецификации'),
        ),
        migrations.AlterField(
            model_name='upd',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=documents.models.get_upd_upload_path, verbose_name='Файл УПД'),
        ),
        migrations.AlterUniqueTogether(
            name='specification',
            unique_together={('contract', 'number')},
        ),
    ]

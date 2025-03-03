# Generated by Django 4.2.7 on 2025-03-03 07:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="color",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="Цвет"
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="taggroup",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="Описание"),
        ),
    ]

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from .models import Client


@receiver(post_save, sender=Client)
def update_search_vector(sender, instance, **kwargs):
    """Автоматическое обновление search_vector после сохранения клиента"""
    Client.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector("name", "company", "phone", "email", "inn", config="russian")
    )
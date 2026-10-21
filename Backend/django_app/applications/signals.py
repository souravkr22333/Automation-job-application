# backend/django_app/applications/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import ApplicationQueue, Application

@receiver(post_save, sender=ApplicationQueue)
def clear_queue_cache_on_save(sender, instance, **kwargs):
    """Clear queue cache when a queue item is saved"""
    cache_key = f'queue_{instance.user_id}'
    cache.delete(cache_key)
    cache.delete(f'queue_stats_{instance.user_id}')

@receiver(post_delete, sender=ApplicationQueue)
def clear_queue_cache_on_delete(sender, instance, **kwargs):
    """Clear queue cache when a queue item is deleted"""
    cache_key = f'queue_{instance.user_id}'
    cache.delete(cache_key)
    cache.delete(f'queue_stats_{instance.user_id}')

@receiver(post_save, sender=Application)
def clear_application_cache_on_save(sender, instance, **kwargs):
    """Clear application cache when an application is saved"""
    cache_key = f'applications_{instance.user_id}'
    cache.delete(cache_key)
    cache.delete(f'application_stats_{instance.user_id}')
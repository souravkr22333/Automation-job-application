# backend/django_app/jobs/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import JobListing

@receiver(post_save, sender=JobListing)
def clear_job_cache_on_save(sender, instance, **kwargs):
    """Clear cache when job is saved"""
    cache.delete(f'job_{instance.id}')
    cache.delete(f'user_jobs_{instance.user_id}')
    cache.delete(f'user_jobs_stats_{instance.user_id}')

@receiver(post_delete, sender=JobListing)
def clear_job_cache_on_delete(sender, instance, **kwargs):
    """Clear cache when job is deleted"""
    cache.delete(f'job_{instance.id}')
    cache.delete(f'user_jobs_{instance.user_id}')
    cache.delete(f'user_jobs_stats_{instance.user_id}')
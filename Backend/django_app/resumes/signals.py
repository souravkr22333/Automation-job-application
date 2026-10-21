# backend/django_app/resumes/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Resume

@receiver(post_save, sender=Resume)
def clear_resume_cache_on_save(sender, instance, **kwargs):
    """Clear resume cache when a resume is saved"""
    cache.delete(f'resume_{instance.id}')
    cache.delete(f'resumes_{instance.user_id}')
    
    if instance.is_default:
        cache.delete(f'default_resume_{instance.user_id}')

@receiver(post_delete, sender=Resume)
def clear_resume_cache_on_delete(sender, instance, **kwargs):
    """Clear resume cache when a resume is deleted"""
    cache.delete(f'resume_{instance.id}')
    cache.delete(f'resumes_{instance.user_id}')
    cache.delete(f'default_resume_{instance.user_id}')


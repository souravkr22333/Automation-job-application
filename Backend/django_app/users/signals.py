# backend/django_app/users/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import User

@receiver(post_save, sender=User)
def clear_user_cache_on_save(sender, instance, **kwargs):
    """Clear user cache when user is saved"""
    cache.delete(f'user_{instance.id}')
    cache.delete(f'user_preferences_{instance.id}')

@receiver(post_delete, sender=User)
def clear_user_cache_on_delete(sender, instance, **kwargs):
    """Clear user cache when user is deleted"""
    cache.delete(f'user_{instance.id}')
    cache.delete(f'user_preferences_{instance.id}')

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    """Handle user login events"""
    # Clear any cached data for this user
    cache.delete(f'user_{user.id}')
    cache.delete(f'user_preferences_{user.id}')
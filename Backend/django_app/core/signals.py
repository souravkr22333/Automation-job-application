# backend/django_app/core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import AuditLog
from users.models import User
import uuid
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events"""
    AuditLog.objects.create(
        user_id=user.id,
        action=AuditLog.Action.LOGIN,
        resource_type='user',
        resource_id=user.id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.path,
        request_method=request.method
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events"""
    if user:
        AuditLog.objects.create(
            user_id=user.id,
            action=AuditLog.Action.LOGOUT,
            resource_type='user',
            resource_id=user.id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_path=request.path,
            request_method=request.method
        )


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user creation"""
    if created:
        AuditLog.objects.create(
            user_id=instance.id,
            action=AuditLog.Action.CREATE,
            resource_type='user',
            resource_id=instance.id,
            changes={'email': instance.email, 'name': instance.name}
        )
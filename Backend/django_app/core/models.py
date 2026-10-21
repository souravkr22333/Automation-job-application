# backend/django_app/core/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Outbox(models.Model):
    """
    Transactional outbox pattern for reliable task queueing.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'
    
    class EventType(models.TextChoices):
        USER_CREATED = 'user_created', 'User Created'
        RESUME_UPLOADED = 'resume_uploaded', 'Resume Uploaded'
        JOB_DISCOVERED = 'job_discovered', 'Job Discovered'
        APPLICATION_SUBMITTED = 'application_submitted', 'Application Submitted'
        APPLICATION_FAILED = 'application_failed', 'Application Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    document_type = models.CharField(max_length=50, db_index=True)
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_outbox'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['document_id', 'document_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.document_type}:{self.document_id} - {self.status}"


class AuditLog(models.Model):
    """
    Comprehensive audit logging.
    """
    
    class Action(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        REGISTER = 'register', 'Register'
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        API_CALL = 'api_call', 'API Call'
        SYSTEM_ERROR = 'system_error', 'System Error'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_email = models.EmailField(blank=True)
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.UUIDField(null=True, blank=True, db_index=True)
    resource_name = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    changes = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'core_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'action']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        user = self.user_email or self.user_id or 'Anonymous'
        return f"{self.action} - {self.resource_type} - {user} - {self.created_at}"


class SystemConfig(models.Model):
    """
    System configuration settings.
    """
    
    class ConfigType(models.TextChoices):
        STRING = 'string', 'String'
        INTEGER = 'integer', 'Integer'
        BOOLEAN = 'boolean', 'Boolean'
        JSON = 'json', 'JSON'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    type = models.CharField(max_length=20, choices=ConfigType.choices, default=ConfigType.STRING)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general', db_index=True)
    is_active = models.BooleanField(default=True)
    is_secret = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_system_config'
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key} = {self.value[:50]}..."


class FeatureFlag(models.Model):
    """
    Feature flags for gradual rollout.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)
    rollout_percentage = models.IntegerField(default=100)
    user_whitelist = models.JSONField(default=list)
    user_blacklist = models.JSONField(default=list)
    targeting_rules = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_feature_flags'
        ordering = ['name']
    
    def __str__(self):
        status = "✅ Enabled" if self.is_enabled else "❌ Disabled"
        return f"{self.name} - {status}"


class SystemNotification(models.Model):
    """
    System notifications for users.
    """
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'
    
    class Type(models.TextChoices):
        INFO = 'info', 'Information'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    action_url = models.URLField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        user = self.user.email if self.user else 'System'
        return f"{self.type} - {user} - {self.title}"
# backend/django_app/core/admin.py
from django.contrib import admin
from .models import AuditLog, SystemConfig, FeatureFlag, SystemNotification

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log Admin"""
    
    list_display = ('action', 'resource_type', 'user_email', 'ip_address', 'status_code', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('user_email', 'resource_name', 'request_path')
    readonly_fields = ('id', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """System Config Admin"""
    
    list_display = ('key', 'value_display', 'type', 'category', 'is_active', 'is_secret')
    list_filter = ('type', 'category', 'is_active', 'is_secret')
    search_fields = ('key', 'description')
    
    def value_display(self, obj):
        if obj.is_secret:
            return '********'
        return obj.value[:50]
    value_display.short_description = 'Value'


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Feature Flag Admin"""
    
    list_display = ('name', 'is_enabled', 'rollout_percentage', 'created_at')
    list_filter = ('is_enabled', 'created_at')
    search_fields = ('name', 'description')


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    """System Notification Admin"""
    
    list_display = ('title', 'user', 'type', 'priority', 'is_read', 'created_at')
    list_filter = ('type', 'priority', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('id', 'created_at')
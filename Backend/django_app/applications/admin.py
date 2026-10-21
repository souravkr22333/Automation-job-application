# backend/django_app/applications/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ApplicationQueue, Application, CoverLetter

@admin.register(ApplicationQueue)
class ApplicationQueueAdmin(admin.ModelAdmin):
    """Application Queue Admin"""
    
    list_display = ('id', 'user', 'job', 'status', 'priority', 'position', 'attempts', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('user__email', 'job__title', 'job__company')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'job', 'priority', 'position')
        }),
        ('Application Materials', {
            'fields': ('tailored_resume', 'cover_letter')
        }),
        ('Status', {
            'fields': ('status', 'attempts', 'max_attempts', 'last_attempt_at', 'error_message')
        }),
        ('Submission', {
            'fields': ('submitted_at', 'application_url', 'notes')
        }),
        ('Metadata', {
            'fields': ('idempotency_key', 'source', 'created_at', 'updated_at')
        })
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Application Admin"""
    
    list_display = ('id', 'user', 'job', 'status', 'applied_at', 'updated_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__email', 'job__title', 'job__company')
    readonly_fields = ('id', 'applied_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'job')
        }),
        ('Application Materials', {
            'fields': ('resume', 'cover_letter')
        }),
        ('Status', {
            'fields': ('status', 'application_url', 'notes')
        }),
        ('Interview', {
            'fields': ('interview_date', 'interview_notes')
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at')
        })
    )


@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    """Cover Letter Admin"""
    
    list_display = ('id', 'user', 'job', 'tone', 'version', 'is_used', 'created_at')
    list_filter = ('tone', 'is_used', 'created_at')
    search_fields = ('user__email', 'job__title', 'job__company')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'job')
        }),
        ('Content', {
            'fields': ('content', 'tone')
        }),
        ('Status', {
            'fields': ('version', 'is_used', 'used_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
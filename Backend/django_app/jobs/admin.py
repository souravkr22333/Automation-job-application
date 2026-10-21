# backend/django_app/jobs/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import JobListing, JobSearchHistory 

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    """Job Listing Admin"""
    
    list_display = ('title', 'company', 'source', 'user', 'match_score', 'status', 'is_applied', 'discovered_at')
    list_filter = ('source', 'status', 'is_applied', 'is_saved', 'is_remote', 'discovered_at')
    search_fields = ('title', 'company', 'location', 'description')
    readonly_fields = ('id', 'discovered_at', 'saved_at', 'applied_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title',  'company_logo', 'url', 'apply_url', 'source', 'source_display')
        }),
        ('Job Details', {
            'fields': ('description', 'location', 'salary', 'salary_min', 'salary_max', 'salary_currency')
        }),
        ('company Detail',{
            'fields':('company','company_description','company_website','company_slogan','employees_count','company_linkedin_url')
        }),
        ('Job Metadata', {
            'fields': ('is_remote', 'employment_type', 'experience_required')
        }),
        ('AI Analysis', {
            'fields': ('match_score', 'missing_skills', 'fit_analysis', 'recommended_keywords','strengths')
        }),
        ('Status', {
            'fields': ('user', 'status', 'is_active', 'is_applied', 'is_saved', 'is_viewed')
        }),
        ('Timestamps', {
            'fields': ('discovered_at', 'saved_at', 'applied_at', 'updated_at')
        })
    )


@admin.register(JobSearchHistory)
class JobSearchHistoryAdmin(admin.ModelAdmin):
    """Job Search History Admin"""
    
    list_display = ('user', 'keywords_display', 'location', 'jobs_found', 'jobs_saved', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'keywords')
    readonly_fields = ('id', 'created_at')
    
    def keywords_display(self, obj):
        return ', '.join(obj.keywords[:3]) if obj.keywords else 'None'
    keywords_display.short_description = 'Keywords'




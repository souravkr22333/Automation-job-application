# backend/django_app/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Education, Experience, Project, Certification, Language


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'phone', 'is_active', 'is_verified', 'created_at')
    list_filter = ('is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'name', 'username', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'username', 'name', 'phone', 'profile_picture', 
                'bio', 'professional_summary','dob', 'address','gender'
            )
        }),
        ('Job Preferences', {
            'fields': (
                'preferred_job_titles', 
                'preferred_locations',
                'skills'
            )
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'email_verified')
        }),
        ('Preferences', {
            'fields': ('preferences',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'password1', 'password2'),
        }),
    )
    
    ordering = ('email',)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution_name', 'degree_name', 'degree_type', 'obtained_marks', 'start_date', 'end_date')
    list_filter = ('degree_type', 'is_current', 'grade_type')
    search_fields = ('user__email', 'user__name', 'institution_name', 'degree_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'job_title', 'employment_type', 'start_date', 'end_date', 'is_current')
    list_filter = ('employment_type', 'is_current', 'experience_level')
    search_fields = ('user__email', 'user__name', 'company_name', 'job_title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'project_type', 'status', 'start_date', 'end_date')
    list_filter = ('project_type', 'status', 'is_current')
    search_fields = ('user__email', 'user__name', 'name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'issuing_organization', 'level', 'issue_date', 'is_valid')
    list_filter = ('level', 'is_lifetime', 'is_expired')
    search_fields = ('user__email', 'user__name', 'name', 'issuing_organization')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-issue_date',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'proficiency', 'is_native')
    list_filter = ('proficiency', 'is_native')
    search_fields = ('user__email', 'user__name', 'name')




# # backend/django_app/users/admin.py
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.html import format_html
# from .models import User, UserActivityLog

# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     """Custom User Admin"""
    
#     list_display = ('email', 'name', 'is_active', 'is_email_verified', 'last_login', 'created_at')
#     list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'created_at')
#     search_fields = ('email', 'name', 'username', 'phone')
#     readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')
#     ordering = ('-created_at',)
    
#     fieldsets = (
#         ('Authentication', {
#             'fields': ('id', 'email', 'username', 'password')
#         }),
#         ('Personal Information', {
#             'fields': ('name', 'phone', 'avatar')
#         }),
#         ('Preferences', {
#             'fields': ('preferences', 'job_search_preferences')
#         }),
#         ('OAuth', {
#             'fields': ('linkedin_token', 'google_token', 'github_token', 'supabase_id')
#         }),
#         ('Status', {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified')
#         }),
#         ('Timestamps', {
#             'fields': ('last_login', 'last_active_at', 'email_verified_at', 'created_at', 'updated_at')
#         }),
#     )
    
#     add_fieldsets = (
#         ('Create User', {
#             'fields': ('email', 'username', 'name', 'password1', 'password2')
#         }),
#     )
    
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related()


# @admin.register(UserActivityLog)
# class UserActivityLogAdmin(admin.ModelAdmin):
#     """User Activity Log Admin"""
    
#     list_display = ('user', 'activity_type', 'created_at')
#     list_filter = ('activity_type', 'created_at')
#     search_fields = ('user__email',)
#     readonly_fields = ('id', 'created_at')
    
#     fieldsets = (
#         ('Activity', {
#             'fields': ('user', 'activity_type', 'metadata')
#         }),
#         ('Context', {
#             'fields': ('ip_address', 'user_agent')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at',)
#         }),
#     )
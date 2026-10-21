from django.contrib import admin
from django.utils.html import format_html, mark_safe

from .models import Resume, TailoredResume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name_display',
        'user_email',
        'file_type_display',
        'file_size_display',
        'is_default_display',
        'parsed_display',
        'processed_display',
        'view_file_link',
    )

    list_filter = ('is_default', 'file_type', 'updated_at')

    search_fields = (
        'id',
        'name',
        'user__email',
        'user__username',
        'user__name',
        'supabase_url',
        'supabase_path',
    )

    list_select_related = ('user',)
    list_per_page = 25

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'file_type', 'file_size_display_readonly'),
            'classes': ('wide',),
        }),
        ('File Information', {
            'fields': ('supabase_url', 'supabase_path', 'view_file_button'),
            'classes': ('wide',),
        }),
         ('Parsed text', {
            'fields': ('parsed_text', 'extracted_skills', 'extracted_experience', 'extracted_job_titles'),
            'classes': ('wide',),
        }),

        ('Processing Flags', {
            'fields': ('is_default', 'version', 'is_parsed', 'is_processed', 'ats_score'),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': (),
            'classes': ('wide', 'collapse'),
        }),
    )

    readonly_fields = (
        'id',
        'file_size_display_readonly',
        'view_file_button',
        'parsed_text_readonly',
    )

    actions = [
        'set_as_default',
        'mark_as_parsed_action',
        'mark_as_processed_action',
    ]

    def name_display(self, obj):
        return obj.name[:47] + '...' if len(obj.name) > 50 else obj.name

    name_display.short_description = 'Name'
    name_display.admin_order_field = 'name'

    def user_email(self, obj):
        return obj.user.email if obj.user else 'No User'

    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def file_type_display(self, obj):
        colors = {'pdf': '#2ecc71', 'docx': '#3498db', 'doc': '#3498db'}
        color = colors.get(obj.file_type, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.file_type.upper() if obj.file_type else 'N/A',
        )

    file_type_display.short_description = 'Type'

    def file_size_display(self, obj):
        if not obj.file_size:
            return '0 B'
        size = float(obj.file_size)
        units = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"

    file_size_display.short_description = 'Size'
    file_size_display.admin_order_field = 'file_size'

    def file_size_display_readonly(self, obj):
        return self.file_size_display(obj)

    file_size_display_readonly.short_description = 'File Size'

    def is_default_display(self, obj):
        if obj.is_default:
            return mark_safe('<span style="color: #2ecc71;">✅ Default</span>')
        return mark_safe('<span style="color: #95a5a6;">⬜ Not Default</span>')

    is_default_display.short_description = 'Default'
    is_default_display.admin_order_field = 'is_default'

    def parsed_display(self, obj):
        if obj.is_parsed:
            return mark_safe('<span style="color: #3498db; font-weight:600;">Parsed</span>')
        return mark_safe('<span style="color: #95a5a6;">Not parsed</span>')

    parsed_display.short_description = 'Parsed'

    def processed_display(self, obj):
        if obj.is_processed:
            return mark_safe('<span style="color: #2ecc71; font-weight:600;">Processed</span>')
        return mark_safe('<span style="color: #95a5a6;">Not processed</span>')

    processed_display.short_description = 'Processed'

    def view_file_link(self, obj):
        if obj.supabase_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3498db;">🔗 View File</a>',
                obj.supabase_url,
            )
        return 'No File'

    view_file_link.short_description = 'File'

    def view_file_button(self, obj):
        if obj.supabase_url:
            return format_html(
                '<a href="{}" target="_blank" class="button" '
                'style="background: #3498db; color: white; padding: 5px 15px; '
                'border-radius: 4px; text-decoration: none; display: inline-block;">'
                '📄 View Resume</a>',
                obj.supabase_url,
            )
        return 'No file uploaded'

    view_file_button.short_description = 'View Resume'

    def parsed_text_readonly(self, obj):
        if not obj.parsed_text:
            return '—'
        return (obj.parsed_text[:200] + '...') if len(obj.parsed_text) > 200 else obj.parsed_text

    parsed_text_readonly.short_description = 'Parsed text preview'

    def set_as_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one resume.', level='warning')
            return
        resume = queryset.first()
        if resume:
            Resume.objects.filter(user=resume.user, is_default=True).exclude(id=resume.id).update(is_default=False)
            resume.is_default = True
            resume.save(update_fields=['is_default'])
            self.message_user(request, f'Resume "{resume.name}" set as default!', level='success')

    set_as_default.short_description = 'Set as default resume'

    def mark_as_parsed_action(self, request, queryset):
        for r in queryset:
            r.mark_as_parsed()
        self.message_user(request, 'Selected resumes marked as parsed.', level='success')

    mark_as_parsed_action.short_description = 'Mark as parsed'

    def mark_as_processed_action(self, request, queryset):
        for r in queryset:
            r.mark_as_processed()
        self.message_user(request, 'Selected resumes marked as processed.', level='success')

    mark_as_processed_action.short_description = 'Mark as processed'


@admin.register(TailoredResume)
class TailoredResumeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'user_email',
        'job_title',
        'job_company',
        'is_used_display',
        'file_size_display',
        'created_at',
        'view_file_link',
    )

    list_filter = ('is_used', 'created_at')

    search_fields = (
        'id',
        'name',
        'user__email',
        'user__username',
        'job__title',
        'job__company',
        'supabase_url',
        'supabase_path',
    )

    list_select_related = ('user', 'job', 'original_resume')
    list_per_page = 25

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'job', 'original_resume'),
            'classes': ('wide',),
        }),
        ('File Information', {
            'fields': ('supabase_url', 'supabase_path', 'file_size', 'file_type', 'view_file_button'),
            'classes': ('wide',),
        }),
        ('Tailored Content', {
            'fields': ('tailored_text_preview', 'changes_summary', 'keywords_added'),
            'classes': ('wide',),
        }),
        ('Status', {
            'fields': ('is_used',),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'file_size_display',
        'view_file_button',
        'tailored_text_preview',
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'No User'
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def job_title(self, obj):
        return obj.job.title if obj.job else 'N/A'
    job_title.short_description = 'Job Title'
    job_title.admin_order_field = 'job__title'

    def job_company(self, obj):
        return obj.job.company if obj.job else 'N/A'
    job_company.short_description = 'Company'
    job_company.admin_order_field = 'job__company'

    def file_size_display(self, obj):
        if not obj.file_size:
            return '0 B'
        size = float(obj.file_size)
        units = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"
    file_size_display.short_description = 'Size'

    def is_used_display(self, obj):
        if obj.is_used:
            return mark_safe('<span style="color: #e74c3c; font-weight:600;">✅ Used</span>')
        return mark_safe('<span style="color: #95a5a6;">⬜ Unused</span>')
    is_used_display.short_description = 'Used'
    is_used_display.admin_order_field = 'is_used'

    def view_file_link(self, obj):
        if obj.supabase_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3498db;">🔗 View PDF</a>',
                obj.supabase_url,
            )
        return 'No File'
    view_file_link.short_description = 'File'

    def view_file_button(self, obj):
        if obj.supabase_url:
            return format_html(
                '<a href="{}" target="_blank" class="button" '
                'style="background: #3498db; color: white; padding: 5px 15px; '
                'border-radius: 4px; text-decoration: none; display: inline-block;">'
                '📄 View Tailored Resume</a>',
                obj.supabase_url,
            )
        return 'No file uploaded'
    view_file_button.short_description = 'View PDF'

    def tailored_text_preview(self, obj):
        if not obj.tailored_text:
            return '—'
        return obj.tailored_text[:300] + '...' if len(obj.tailored_text) > 300 else obj.tailored_text
    tailored_text_preview.short_description = 'Tailored Text Preview'


# backend/django_app/jobs/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import JobListing, JobSearchHistory


class JobListingSerializer(serializers.ModelSerializer):
    """Job listing serialization with computed fields"""

    match_score_display = serializers.SerializerMethodField()
    days_ago = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    is_applied_display = serializers.SerializerMethodField()
    source_icon = serializers.SerializerMethodField()
    source_color = serializers.SerializerMethodField()

    # Company detail fields (stored directly on JobListing)
    company_website = serializers.SerializerMethodField()
    company_slogan = serializers.SerializerMethodField()
    company_description = serializers.SerializerMethodField()
    company_employees_count = serializers.SerializerMethodField()
    company_linkedin_url = serializers.SerializerMethodField()

    # Tailored resume for this job (if any)
    tailored_resume = serializers.SerializerMethodField()


    class Meta:
        model = JobListing
        fields = (
            'id', 'title', 'company', 'company_logo',


            # expanded company detail fields used by frontend
            'company_website',
            'company_slogan',
            'company_description',
            'company_employees_count',
            'company_linkedin_url',

            'description',
            'url', 'apply_url',
            'source', 'source_display', 'source_icon', 'source_color',
            'location',
            'salary', 'salary_min', 'salary_max',
            'salary_currency', 'posted_date', 'expires_date',
            'match_score', 'match_score_display',
            'missing_skills',
            'fit_analysis', 'recommended_keywords',
            'required_skills', 'preferred_skills', 'key_responsibilities',
            'is_active', 'is_applied', 'is_applied_display', 'is_saved',
            'is_remote', 'is_viewed', 'employment_type',
            'status', 'status_display', 'experience_required',
            'discovered_at', 'saved_at', 'applied_at', 'updated_at',
            'days_ago',
            'tailored_resume',
        )
        read_only_fields = ('id', 'discovered_at', 'saved_at', 'applied_at', 'updated_at')

    def get_tailored_resume(self, obj):
        """Return tailored resume info if one exists for this job+user"""
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return None
            tailored = obj.tailored_resume_files.filter(user=request.user).first()
            if tailored and tailored.supabase_url:
                return {
                    'id': str(tailored.id),
                    'name': tailored.name,
                    'supabase_url': tailored.supabase_url,
                    'created_at': tailored.created_at.isoformat() if tailored.created_at else None,
                }
        except Exception:
            pass
        return None

    def get_company_website(self, obj):
        return getattr(obj, 'company_website', None)

    def get_company_slogan(self, obj):
        return getattr(obj, 'company_slogan', None)

    def get_company_description(self, obj):
        return getattr(obj, 'company_description', None)

    def get_company_employees_count(self, obj):
        return getattr(obj, 'employees_count', None)

    def get_company_linkedin_url(self, obj):
        return getattr(obj, 'company_linkedin_url', None)


    def get_match_score_display(self, obj):
        if obj.match_score is not None:
            return f"{int(obj.match_score)}%"
        return "N/A"

    def get_days_ago(self, obj):
        if obj.discovered_at:
            days = (timezone.now() - obj.discovered_at).days
            if days == 0:
                return "Today"
            if days == 1:
                return "Yesterday"
            if days < 7:
                return f"{days} days ago"
            if days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            return obj.discovered_at.strftime("%b %d, %Y")
        return ""

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_is_applied_display(self, obj):
        return "Applied" if obj.is_applied else "Not Applied"

    def get_source_icon(self, obj):
        icons = {
            'linkedin': 'in',
            'indeed': 'id',
            'glassdoor': 'gd',
            'google': 'go',
            'ziprecruiter': 'zr',
            'unknown': '📌',
        }
        return icons.get(obj.source, '📌')

    def get_source_color(self, obj):
        colors = {
            'linkedin': '#0A66C2',
            'indeed': '#003D9B',
            'glassdoor': '#00A162',
            'google': '#4285F4',
            'ziprecruiter': '#0C52A8',
            'unknown': '#6B7280',
        }
        return colors.get(obj.source, '#6B7280')


class JobDiscoverySerializer(serializers.Serializer):
    """Job discovery request validation"""

    job_titles = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=[],
    )
    location = serializers.CharField(default='United States', required=False)
    max_jobs = serializers.IntegerField(min_value=10, max_value=200, default=30)
    sources = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[
                'google_jobs',
                'indeed_rss',
                'apify_linkedin',
                'apify_indeed',
                'apify_naukri',
            ],
        ),
        default=['google_jobs', 'indeed_rss'],
        required=False,
    )
    remote_only = serializers.BooleanField(default=False)


class JobApplySerializer(serializers.Serializer):
    """Apply to job validation"""

    job_id = serializers.UUIDField(required=True)
    resume_id = serializers.UUIDField(required=False)
    tone = serializers.ChoiceField(
        choices=['professional', 'enthusiastic', 'concise', 'casual'],
        default='professional',
    )


class JobSearchHistorySerializer(serializers.ModelSerializer):
    """Search history serialization"""

    class Meta:
        model = JobSearchHistory
        fields = (
            'id', 'keywords', 'location', 'sources',
            'jobs_found', 'jobs_saved', 'search_params', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

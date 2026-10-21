# backend/django_app/resumes/serializers.py
import json
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Resume, ResumeVersion, TailoredResume 

class ResumeVersionSerializer(serializers.ModelSerializer):
    """Resume version serialization"""
    
    class Meta:
        model = ResumeVersion
        fields = [
            'id', 'version_number', 'version_name', 'parsed_text',
            'extracted_skills', 'extracted_experience', 'extracted_job_titles',
            'changes_summary', 'change_reason', 'job', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ResumeSerializer(serializers.ModelSerializer):
    """Resume serialization with complete details"""
    
    versions_count = serializers.SerializerMethodField()
    tailored_versions_count = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'user', 'user_email', 'user_name', 'name',
            'supabase_url', 'supabase_path', 'supabase_bucket',
            'file_size', 'file_type',
            'parsed_text', 'extracted_skills', 'extracted_experience',
            'extracted_job_titles', 'extracted_education', 'extracted_certifications',
            'is_default', 'version', 'is_tailored', 'tailored_for_job',
            'tailored_from', 'changes_summary',
            'ats_score', 'ats_issues', 'ats_recommendations',
            'is_parsed', 'is_processed',
            'uploaded_at', 'parsed_at', 'processed_at', 'updated_at',
            'versions_count', 'tailored_versions_count'
        ]
        read_only_fields = [
            'id', 'user', 'supabase_url', 'supabase_path', 'supabase_bucket',
            'file_size', 'file_type', 'version', 'is_tailored',
            'is_parsed', 'is_processed', 'uploaded_at', 'parsed_at',
            'processed_at', 'updated_at', 'versions_count', 'tailored_versions_count',
            'user_email', 'user_name'
        ]
        extra_kwargs = {
            'parsed_text': {'required': False},
            'extracted_skills': {'required': False},
            'extracted_job_titles': {'required': False},
        }
    
    def get_versions_count(self, obj):
        return obj.versions.count()
    
    def get_tailored_versions_count(self, obj):
        return obj.tailored_versions.count()
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_user_name(self, obj):
        return obj.user.name
    
    def validate(self, data):
        # Ensure only one default resume per user
        if data.get('is_default', False):
            user = self.context['request'].user
            if Resume.objects.filter(user=user, is_default=True).exclude(
                id=self.instance.id if self.instance else None
            ).exists():
                raise ValidationError({
                    'is_default': 'User already has a default resume.'
                })
        return data


class ResumeUploadSerializer(serializers.Serializer):
    """Resume upload validation serializer"""
    
    file = serializers.FileField(
        required=True,
        help_text="Resume file (PDF or DOCX)"
    )
    name = serializers.CharField(
        required=False,
        max_length=255,
        help_text="Custom name for the resume"
    )
    is_default = serializers.BooleanField(
        default=True,
        help_text="Set as default resume"
    )
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check size (5MB max)
        if value.size > 5 * 1024 * 1024:
            raise ValidationError("File size must be under 5MB.")
        
        # Check content type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        if value.content_type not in allowed_types:
            raise ValidationError("Only PDF and DOCX files are supported.")
        
        # Check extension
        ext = value.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx', 'doc']:
            raise ValidationError("Only .pdf, .docx, and .doc files are supported.")
        
        return value


class ResumeTailorSerializer(serializers.Serializer):
    """Resume tailoring request serializer"""
    
    job_id = serializers.UUIDField(
        required=True,
        help_text="ID of the job to tailor for"
    )
    resume_id = serializers.UUIDField(
        required=False,
        help_text="ID of the resume to tailor (uses default if not provided)"
    )


class ResumeATSCheckSerializer(serializers.Serializer):
    """ATS check request serializer"""
    
    job_description = serializers.CharField(
        required=True,
        help_text="Job description to check against"
    )


class ResumeDeleteSerializer(serializers.Serializer):
    """Bulk delete serializer"""
    
    resume_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of resume IDs to delete"
    )


class TailoredResumeSerializer(serializers.ModelSerializer):
    """TailoredResume serialization"""
    job_title = serializers.SerializerMethodField()
    job_company = serializers.SerializerMethodField()

    class Meta:
        model = TailoredResume
        fields = [
            'id', 'user', 'job', 'job_title', 'job_company',
            'original_resume', 'name', 'supabase_url', 'supabase_path',
            'supabase_bucket', 'file_size', 'file_type',
            'tailored_text', 'changes_summary', 'keywords_added',
            'is_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_job_title(self, obj):
        return obj.job.title if obj.job else None

    def get_job_company(self, obj):
        return obj.job.company if obj.job else None


class TailoredResumeEditSerializer(serializers.Serializer):
    """Serializer for saving edited tailored resume text"""
    tailored_text = serializers.CharField(
        required=True,
        help_text="The edited resume text to save"
    )


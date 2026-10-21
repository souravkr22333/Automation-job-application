# backend/django_app/applications/serializers.py
from rest_framework import serializers
from .models import ApplicationQueue, Application, CoverLetter
from jobs.serializers import JobListingSerializer
from resumes.serializers import ResumeSerializer, TailoredResumeSerializer

class ApplicationQueueSerializer(serializers.ModelSerializer):
    """Application queue serialization"""
    job_details = JobListingSerializer(source='job', read_only=True)
    tailored_resume_details = TailoredResumeSerializer(source='tailored_resume', read_only=True)
    
    class Meta:
        model = ApplicationQueue
        fields = (
            'id', 'user', 'job', 'job_details', 'priority', 'position',
            'tailored_resume', 'tailored_resume_details',
            'cover_letter',
            'status', 'attempts', 'max_attempts', 'last_attempt_at',
            'error_message', 'submitted_at', 'application_url', 'notes',
            'idempotency_key', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'position')


class ApplicationQueueCreateSerializer(serializers.Serializer):
    """Create queue items"""
    job_ids = serializers.ListField(child=serializers.UUIDField(), required=True)


class ApplicationQueueReorderSerializer(serializers.Serializer):
    """Reorder queue items"""
    ordered_ids = serializers.ListField(child=serializers.UUIDField(), required=True)


class ApplicationSerializer(serializers.ModelSerializer):
    """Application serialization"""
    job_details = JobListingSerializer(source='job', read_only=True)
    resume_details = ResumeSerializer(source='resume', read_only=True)
    
    class Meta:
        model = Application
        fields = (
            'id', 'user', 'job', 'job_details', 'resume', 'resume_details',
            'cover_letter', 'status', 'applied_at', 'updated_at',
            'application_url', 'notes', 'interview_date', 'interview_notes'
        )
        read_only_fields = ('id', 'applied_at', 'updated_at')


class CoverLetterSerializer(serializers.ModelSerializer):
    """Cover letter serialization"""
    
    class Meta:
        model = CoverLetter
        fields = (
            'id', 'user', 'job', 'content', 'tone',
            'version', 'is_used', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'version')


class CoverLetterGenerateSerializer(serializers.Serializer):
    """Cover letter generation request"""
    job_id = serializers.UUIDField(required=True)
    resume_id = serializers.UUIDField(required=False)
    tone = serializers.ChoiceField(
        choices=['professional', 'enthusiastic', 'concise', 'casual'],
        default='professional'
    )
    additional_points = serializers.CharField(required=False, allow_blank=True)

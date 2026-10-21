# backend/django_app/applications/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class ApplicationQueue(models.Model):
    """
    Auto-apply queue for processing applications.
    """

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        GENERATING_RESUME = 'generating_resume', 'Generating Resume'
        APPLYING = 'applying', 'Applying'
        RETRYING = 'retrying', 'Retrying'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'
        PAUSED = 'paused', 'Paused'
        LIMIT_REACHED = 'limit_reached', 'Daily limit reached'

    class Priority(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_items'
    )
    job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.CASCADE,
        related_name='queue_items'
    )

    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    position = models.IntegerField(default=0)

    # Application Materials
    tailored_resume = models.ForeignKey(
        'resumes.TailoredResume',
        on_delete=models.SET_NULL,
        null=True,
        related_name='queue_applications',
        help_text="The tailored resume PDF stored in Supabase (TailoredResume)"
    )
    tailored_resume_file = models.ForeignKey(
        'resumes.TailoredResume',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queue_items',
        help_text="The generated PDF/resume file stored in Supabase (deprecated, use tailored_resume)"
    )
    cover_letter = models.TextField(blank=True)
    cover_letter_id = models.UUIDField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Submission Tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    application_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    # Idempotency
    idempotency_key = models.CharField(max_length=255, unique=True)

    # Metadata
    source = models.CharField(max_length=50, default='linkedin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'application_queue'
        ordering = ['position', 'created_at']
        unique_together = [['user', 'job']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['position']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.job.title} at {self.job.company} - {self.status}"


class Application(models.Model):
    """
    Completed application record.
    """

    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        REJECTED = 'rejected', 'Rejected'
        INTERVIEWING = 'interviewing', 'Interviewing'
        OFFER = 'offer', 'Offer'
        ACCEPTED = 'accepted', 'Accepted'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.CASCADE,
        related_name='applications'
    )

    # Application Materials
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.SET_NULL,
        null=True,
        related_name='applications'
    )
    cover_letter = models.TextField(blank=True)
    cover_letter_id = models.UUIDField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tracking
    application_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    # Interview Tracking
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)

    # Feedback
    feedback = models.TextField(blank=True)

    class Meta:
        db_table = 'applications'
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['applied_at']),
            models.Index(fields=['job']),
        ]

    def __str__(self):
        return f"{self.job.title} at {self.job.company} - {self.status}"


class CoverLetter(models.Model):
    """
    Generated cover letters.
    """

    class Tone(models.TextChoices):
        PROFESSIONAL = 'professional', 'Professional'
        ENTHUSIASTIC = 'enthusiastic', 'Enthusiastic'
        CONCISE = 'concise', 'Concise'
        CASUAL = 'casual', 'Casual'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cover_letters'
    )
    job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cover_letters'
    )

    content = models.TextField()
    tone = models.CharField(max_length=20, choices=Tone.choices, default=Tone.PROFESSIONAL)
    version = models.IntegerField(default=1)

    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cover_letters'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_used']),
        ]

    def __str__(self):
        return f"Cover Letter - {self.created_at.strftime('%Y-%m-%d')}"

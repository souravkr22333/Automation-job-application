# backend/django_app/jobs/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone




class JobListing(models.Model):
    """
    Job listing from various sources.
    """
    
    class Source(models.TextChoices):
        LINKEDIN = 'linkedin', 'LinkedIn'
        INDEED = 'indeed', 'Indeed'
        GLASSDOOR = 'glassdoor', 'Glassdoor'
        ZIPRECRUITER = 'ziprecruiter', 'ZipRecruiter'
        MONSTER = 'monster', 'Monster'
        CAREERBUILDER = 'careerbuilder', 'CareerBuilder'
        DICE = 'dice', 'Dice'
        SIMPLYHIRED = 'simplyhired', 'SimplyHired'
        GOOGLE = 'google', 'Google Jobs'
        UNKNOWN = 'unknown', 'Unknown'
    
    class Status(models.TextChoices):
        DISCOVERED = 'discovered', 'Discovered'
        SAVED = 'saved', 'Saved'
        APPLIED = 'applied', 'Applied'
        INTERVIEWING = 'interviewing', 'Interviewing'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source Information
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.UNKNOWN)
    source_display = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=500)
    apply_url = models.URLField(max_length=500, blank=True)
    
    # Job Details
    title = models.CharField(max_length=255, db_index=True)
    company = models.CharField(max_length=255, db_index=True)

    company_website = models.URLField(max_length=500, null=True, blank=True, db_index=True)
    company_slogan = models.TextField(blank=True)
    company_description = models.TextField(blank=True)
    employees_count = models.IntegerField(null=True, blank=True)
    company_linkedin_url = models.URLField(null=True, blank=True, db_index=True)

    company_logo = models.URLField(max_length=500, blank=True)

    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    salary = models.CharField(max_length=100, blank=True)
    salary_min = models.FloatField(null=True, blank=True)
    salary_max = models.FloatField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    posted_date = models.CharField(null=True, blank=True)
    expires_date = models.DateTimeField(null=True, blank=True)
    
    # Job Metadata
    is_remote = models.BooleanField(default=False)
    employment_type = models.CharField(max_length=50, blank=True)
    experience_required = models.CharField(max_length=50, blank=True)
    
    # AI Generated Fields
    match_score = models.FloatField(null=True, blank=True, db_index=True)
    missing_skills = models.JSONField(default=list)
    fit_analysis = models.TextField(blank=True)
    strengths = models.JSONField(default=list, help_text="Candidate's top strengths for this job")
    recommended_keywords = models.JSONField(default=list)
    required_skills = models.JSONField(default=list)
    preferred_skills = models.JSONField(default=list)
    key_responsibilities = models.JSONField(default=list)
    
    # User Relationship
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='job_listings'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCOVERED,
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_applied = models.BooleanField(default=False, db_index=True)
    is_saved = models.BooleanField(default=False, db_index=True)
    is_viewed = models.BooleanField(default=False)
    
    # Timestamps
    discovered_at = models.DateTimeField(auto_now_add=True)
    saved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_listings'
        ordering = ['-match_score', '-discovered_at']
        indexes = [
            models.Index(fields=['user', 'is_applied']),
            models.Index(fields=['user', 'is_saved']),
            models.Index(fields=['user', 'match_score']),
            models.Index(fields=['source']),
            models.Index(fields=['status']),
            models.Index(fields=['title', 'company']),
        ]
        unique_together = [['url', 'user']]
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    def save(self, *args, **kwargs):
        if self.is_saved and not self.saved_at:
            self.saved_at = timezone.now()
        if self.is_applied and not self.applied_at:
            self.applied_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def status_display(self):
        return self.get_status_display()
    
    @property
    def match_score_display(self):
        if self.match_score is not None:
            return f"{int(self.match_score)}%"
        return "N/A"


class JobSearchHistory(models.Model):
    """
    Track user job searches.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_searches'
    )
    keywords = models.JSONField(default=list)
    location = models.CharField(max_length=255)
    sources = models.JSONField(default=list)
    jobs_found = models.IntegerField(default=0)
    jobs_saved = models.IntegerField(default=0)
    search_params = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'job_search_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {', '.join(self.keywords[:3])}"
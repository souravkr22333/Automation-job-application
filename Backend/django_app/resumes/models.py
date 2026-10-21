import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class Resume(models.Model):
    """
    Resume model with Supabase storage integration.
    Each user can have only ONE resume at a time.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # User relationship
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    
    # Basic information
    name = models.CharField(
        max_length=255,
        help_text="Original filename"
    )
    
    # Supabase storage information
    supabase_url = models.URLField(
        max_length=500,
        help_text="Public URL from Supabase"
    )
    supabase_path = models.CharField(
        max_length=500,
        help_text="Path in Supabase storage"

    )
    supabase_bucket = models.CharField(
        max_length=100,
        default='resumes',
        help_text="Supabase bucket name"
    )
    
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    file_type = models.CharField(
        max_length=50,
        default='application/pdf',
        help_text="MIME type of the file"
    )
    
    # Parsed content
    parsed_text = models.TextField(
        blank=True,
        help_text="Extracted text from resume"
    )
    
    # AI extracted information
    extracted_skills = models.JSONField(
        default=list,
        help_text="List of skills extracted from resume"
    )
    extracted_experience = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total years of experience"
    )
    extracted_job_titles = models.JSONField(
        default=list,
        help_text="List of job titles from resume"
    )
    extracted_education = models.JSONField(
        default=list,
        blank=True,
        help_text="List of education entries"
    )
    extracted_certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of certifications"
    )
    
    # Default status
    is_default = models.BooleanField(
        default=True,
        help_text="Whether this is the user's default resume"
    )
    
    # Versioning
    version = models.IntegerField(
        default=1,
        help_text="Resume version number"
    )
    
    # Tailoring information
    is_tailored = models.BooleanField(
        default=False,
        help_text="Whether this is a tailored version"
    )
    tailored_for_job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tailored_resumes',
        help_text="Job this resume was tailored for"
    )
    tailored_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tailored_versions',
        help_text="Original resume this was tailored from"
    )
    changes_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of changes made during tailoring"
    )
    
    # ATS optimization
    ats_score = models.FloatField(
        null=True,
        blank=True,
        help_text="ATS compatibility score (0-100)"
    )
    ats_issues = models.JSONField(
        default=list,
        blank=True,
        help_text="List of ATS issues found"
    )
    ats_recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text="Recommendations for ATS improvement"
    )
    
    # Status flags
    is_parsed = models.BooleanField(
        default=False,
        help_text="Whether the resume has been parsed"
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether AI processing is complete"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the resume was uploaded"
    )
    parsed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the resume was parsed"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When AI processing was completed"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the resume was last updated"
    )
    
    class Meta:
        db_table = 'resumes'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['user', 'uploaded_at']),
            models.Index(fields=['is_tailored']),
            models.Index(fields=['is_processed']),
        ]
        
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'

    def __str__(self):
        return f"{self.name} (v{self.version}) - {self.user.email}"

    def get_file_extension(self) -> str:
        """Get the file extension from the name"""
        return self.name.split('.')[-1].lower() if '.' in self.name else 'pdf'

    def get_filename(self) -> str:
        """Get the filename without extension"""
        return self.name.rsplit('.', 1)[0] if '.' in self.name else self.name

    def mark_as_parsed(self):
        """Mark the resume as parsed"""
        self.is_parsed = True
        self.parsed_at = timezone.now()
        self.save(update_fields=['is_parsed', 'parsed_at'])

    def mark_as_processed(self):
        """Mark the resume as fully processed"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['is_processed', 'processed_at'])

    def get_supabase_url(self) -> str:
        """Get the public URL from Supabase"""
        return self.supabase_url


class ResumeVersion(models.Model):
    """
    Track resume version history for audit and rollback.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    
    # Version information
    version_number = models.IntegerField(
        help_text="Version number"
    )
    version_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional version name/label"
    )
    
    # Content snapshot
    parsed_text = models.TextField(
        blank=True,
        help_text="Parsed text at this version"
    )
    extracted_skills = models.JSONField(
        default=list,
        help_text="Skills at this version"
    )
    extracted_experience = models.IntegerField(
        null=True,
        blank=True,
        help_text="Experience at this version"
    )
    extracted_job_titles = models.JSONField(
        default=list,
        help_text="Job titles at this version"
    )
    
    # Change tracking
    changes_summary = models.JSONField(
        default=dict,
        help_text="Summary of changes from previous version"
    )
    change_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for this version (e.g., 'Tailored for Google')"
    )
    
    # Associated job (if tailored)
    job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Job this version was tailored for"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this version was created"
    )
    
    class Meta:
        db_table = 'resume_versions'
        ordering = ['-version_number']
        unique_together = [['resume', 'version_number']]
        indexes = [
            models.Index(fields=['resume', 'version_number']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Resume Version'
        verbose_name_plural = 'Resume Versions'

    def __str__(self):
        return f"{self.resume.name} - v{self.version_number}"


class TailoredResume(models.Model):
    """
    Tailored resume with PDF stored in Supabase 'Tailored resume' bucket.
    Created when a user clicks "Auto Generate" - the tailored text is converted
    to PDF, uploaded to Supabase, and tracked here for download/application.
    """
    TAILORED_BUCKET = 'Tailored resume'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tailored_resumes'
    )
    job = models.ForeignKey(
        'jobs.JobListing',
        on_delete=models.CASCADE,
        related_name='tailored_resume_files',
        help_text="Job this resume was tailored for"
    )
    original_resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tailored_versions_new',
        help_text="Original resume this was tailored from"
    )

    # File info (stored in 'Tailored resume' bucket)
    name = models.CharField(
        max_length=255,
        help_text="Filename (e.g. 'John_Doe_Google_Software_Engineer.pdf')"
    )
    supabase_url = models.URLField(
        max_length=500,
        help_text="Public URL from Supabase 'Tailored resume' bucket"
    )
    supabase_path = models.CharField(
        max_length=500,
        help_text="Path in Supabase storage (e.g. 'users/{user_id}/{uuid}.pdf')"
    )
    supabase_bucket = models.CharField(
        max_length=100,
        default=TAILORED_BUCKET,
        help_text="Supabase bucket name"
    )
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    file_type = models.CharField(
        max_length=50,
        default='application/pdf',
        help_text="MIME type of the file"
    )

    # Tailored content (plain text)
    tailored_text = models.TextField(
        blank=True,
        help_text="The tailored resume text"
    )
    changes_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of changes made during tailoring"
    )
    keywords_added = models.JSONField(
        default=list,
        blank=True,
        help_text="Keywords added from job description"
    )

    # Status
    is_used = models.BooleanField(
        default=False,
        help_text="Whether this tailored resume has been used in an application"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tailored_resumes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['job']),
            models.Index(fields=['is_used']),
        ]
        verbose_name = 'Tailored Resume'
        verbose_name_plural = 'Tailored Resumes'

    def __str__(self):
        return f"Tailored: {self.name} (v{self.created_at.strftime('%Y-%m-%d')})"

    def get_filename(self) -> str:
        """Get the filename without extension"""
        return self.name.rsplit('.', 1)[0] if '.' in self.name else self.name

    def get_supabase_url(self) -> str:
        """Get the public URL from Supabase"""
        return self.supabase_url

# backend/django_app/users/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):

    class JobType(models.TextChoices):
        PART_TIME = "Part time" , "part time"
        FULL_TIME = "Full time" , "Full time"
        INTERNSHIP = "Internship" , "internship"
        FREELANCE = "Freelance" , "freelance"

    
    class Workmode(models.TextChoices):
        HYBRID = "Hybrid" , "hybrid"
        REMOTE = "Remote" , "remote"
        ONSITE = "Onsite" , "onsite"
        ANY = "Any" , "any"

    class genders(models.TextChoices):
        MALE = "male","Male" 
        FEMALE = "female" ,"Female" 
        OTHER = "Other","other"
        



    """Custom User model with complete profile and resume sections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.URLField(max_length=500, blank=True)
    bio = models.TextField(blank=True, help_text="Short professional summary")
    dob = models.DateField(blank=True , null=True)
    address = models.CharField(max_length=80, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, choices=genders.choices, default="Male")
    
    # Job preferences (multiple select)
    preferred_job_titles = models.JSONField(
        default=list,
        help_text="List of preferred job titles"
    )
    preferred_locations = models.JSONField(
        default=list,
        help_text="List of preferred locations"
    )
    
    # Skills (multiple select)
    skills = models.JSONField(
        default=list,
        help_text="List of user skills"
    )
    
    # Professional summary
    professional_summary = models.TextField(
        blank=True,
        help_text="Professional summary for resume"
    )

    job_type = models.CharField(max_length=20, null=True,blank=True, choices=JobType.choices)
    work_mode = models.CharField(max_length=20, null=True,blank=True, choices=Workmode.choices)
    
    # Social links
    linkedin_url = models.URLField(max_length=500, blank=True)
    github_url = models.URLField(max_length=500, blank=True)
    portfolio_url = models.URLField(max_length=500, blank=True)
    
    # OAuth tokens
    linkedin_token = models.TextField(blank=True, null=True)
    google_token = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Preferences (JSON)
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name
    
    def get_skills_list(self):
        return self.skills if isinstance(self.skills, list) else []
    
    def get_preferred_jobs(self):
        return self.preferred_job_titles if isinstance(self.preferred_job_titles, list) else []
    
    def get_preferred_locations(self):
        return self.preferred_locations if isinstance(self.preferred_locations, list) else []

    def get_default_resume(self):
        """Get the user's default resume"""
        from resumes.models import Resume
        try:
            return Resume.objects.filter(user=self, is_default=True).first()
        except Resume.DoesNotExist:
            return None


class Education(models.Model):
    """User education details"""
    
    class DegreeType(models.TextChoices):
        HIGH_SCHOOL = 'high_school', 'High School'
        ASSOCIATE = 'associate', 'Associate Degree'
        BACHELORS = 'bachelors', "Bachelor's Degree"
        MASTERS = 'masters', "Master's Degree"
        PHD = 'phd', 'PhD'
        CERTIFICATION = 'certification', 'Certification'
        DIPLOMA = 'diploma', 'Diploma'
        OTHER = 'other', 'Other'
    
    class GradeType(models.TextChoices):
        CGPA = 'cgpa', 'CGPA'
        PERCENTAGE = 'percentage', 'Percentage'
        GPA = 'gpa', 'GPA'
        GRADE = 'grade', 'Grade'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='educations')
    
    # Institution details
    institution_name = models.CharField(max_length=255)
    institution_location = models.CharField(max_length=255, blank=True)
    institution_logo = models.URLField(max_length=500, blank=True)
    
    # Degree details
    degree_type = models.CharField(max_length=20, choices=DegreeType.choices)
    degree_name = models.CharField(max_length=255, help_text="e.g., B.Tech in Computer Science")
    major = models.CharField(max_length=255, blank=True)
    minor = models.CharField(max_length=255, blank=True)
    
    # Marks/Grades
    grade_type = models.CharField(max_length=20, choices=GradeType.choices, default=GradeType.PERCENTAGE)
    obtained_marks = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marks in percentage/CGPA/GPA"
    )
    max_marks = models.FloatField(
        default=100,
        validators=[MinValueValidator(0)],
        help_text="Maximum marks possible"
    )
    grade_scale = models.FloatField(
        default=10,
        help_text="Scale of CGPA/GPA (e.g., 10 for 10-point scale)"
    )
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Additional info
    description = models.TextField(blank=True)
    achievements = models.JSONField(default=list, blank=True)
    courses = models.JSONField(default=list, blank=True)
    activities = models.JSONField(default=list, blank=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_educations'
        ordering = ['-order', '-start_date']
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.degree_name} - {self.institution_name}"
    
    def get_duration(self):
        """Get the duration of education in months"""
        if self.end_date:
            return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        return 0


class Experience(models.Model):
    """User work experience details"""
    
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'
        FREELANCE = 'freelance', 'Freelance'
        REMOTE = 'remote', 'Remote'
        HYBRID = 'hybrid', 'Hybrid'
    
    class ExperienceLevel(models.TextChoices):
        ENTRY = 'entry', 'Entry Level'
        JUNIOR = 'junior', 'Junior'
        MID = 'mid', 'Mid Level'
        SENIOR = 'senior', 'Senior'
        LEAD = 'lead', 'Lead'
        MANAGER = 'manager', 'Manager'
        DIRECTOR = 'director', 'Director'
        EXECUTIVE = 'executive', 'Executive'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    
    # Company details
    company_name = models.CharField(max_length=255)
    company_location = models.CharField(max_length=255, blank=True)
    company_website = models.URLField(max_length=500, blank=True)
    company_logo = models.URLField(max_length=500, blank=True)
    company_industry = models.CharField(max_length=255, blank=True)
    
    # Position details
    job_title = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.MID)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Description
    description = models.TextField(help_text="Detailed description of role and responsibilities")
    achievements = models.JSONField(default=list, help_text="List of key achievements")
    technologies_used = models.JSONField(default=list, help_text="Technologies used in this role")
    
    # Skills used in this experience
    skills_used = models.JSONField(default=list, help_text="Skills used in this role")
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_experiences'
        ordering = ['-order', '-start_date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['company_name']),
        ]
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    def get_duration(self):
        """Get the duration of experience in months"""
        if self.end_date:
            return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        return 0
    
    def get_duration_years(self):
        """Get the duration in years"""
        months = self.get_duration()
        if months > 0:
            return round(months / 12, 1)
        return 0


class Project(models.Model):
    """User project details"""
    
    class ProjectType(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        PROFESSIONAL = 'professional', 'Professional'
        ACADEMIC = 'academic', 'Academic'
        OPEN_SOURCE = 'open_source', 'Open Source'
        FREELANCE = 'freelance', 'Freelance'
        HACKATHON = 'hackathon', 'Hackathon'
    
    class ProjectStatus(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        PLANNED = 'planned', 'Planned'
        ON_HOLD = 'on_hold', 'On Hold'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    # Project details
    name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.PERSONAL)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.COMPLETED)
    
    # Description
    description = models.TextField(help_text="Detailed project description")
    long_description = models.TextField(blank=True, help_text="Extended description")
    
    # Technologies and skills
    technologies = models.JSONField(default=list, help_text="Technologies used")
    skills_used = models.JSONField(default=list, help_text="Skills used in this project")
    
    # Links
    project_url = models.URLField(max_length=500, blank=True)
    github_url = models.URLField(max_length=500, blank=True)
    demo_url = models.URLField(max_length=500, blank=True)
    
    # Images
    cover_image = models.URLField(max_length=500, blank=True)
    screenshots = models.JSONField(default=list, blank=True)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Team
    team_size = models.IntegerField(default=1)
    team_members = models.JSONField(default=list, blank=True, help_text="List of team member names")
    role = models.CharField(max_length=255, blank=True, help_text="Your role in the project")
    
    # Additional info
    achievements = models.JSONField(default=list, blank=True)
    challenges = models.TextField(blank=True)
    learnings = models.TextField(blank=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_projects'
        ordering = ['-order', '-start_date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project_type']),
        ]
    
    def __str__(self):
        return self.name


class Certification(models.Model):
    """User certifications"""
    
    class CertificationLevel(models.TextChoices):
        FOUNDATIONAL = 'foundational', 'Foundational'
        ASSOCIATE = 'associate', 'Associate'
        PROFESSIONAL = 'professional', 'Professional'
        EXPERT = 'expert', 'Expert'
        MASTER = 'master', 'Master'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    
    # Certification details
    name = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=CertificationLevel.choices, default=CertificationLevel.PROFESSIONAL)
    
    # Verification
    credential_id = models.CharField(max_length=255, blank=True)
    credential_url = models.URLField(max_length=500, blank=True)
    verification_url = models.URLField(max_length=500, blank=True)
    
    # Dates
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_lifetime = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    
    # Skills covered
    skills_covered = models.JSONField(default=list, help_text="Skills covered in certification")
    
    # Additional info
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_certifications'
        ordering = ['-order', '-issue_date']
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"
    
    def is_valid(self):
        """Check if certification is still valid"""
        if self.is_lifetime:
            return True
        if self.is_expired:
            return False
        if self.expiry_date:
            return timezone.now().date() <= self.expiry_date
        return True


class Language(models.Model):
    """User language skills"""
    
    class ProficiencyLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        ELEMENTARY = 'elementary', 'Elementary'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        UPPER_INTERMEDIATE = 'upper_intermediate', 'Upper Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        PROFICIENT = 'proficient', 'Proficient'
        NATIVE = 'native', 'Native'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='languages')
    
    # Language details
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=ProficiencyLevel.choices, default=ProficiencyLevel.INTERMEDIATE)
    is_native = models.BooleanField(default=False)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_languages'
        ordering = ['-order', '-proficiency']
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.proficiency}"





# backend/fastapi_app/models/schemas.py
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobSource(str, Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    MANUAL = "manual"


class JobStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"


class UserPreferences(BaseModel):
    job_titles: List[str] = []
    locations: List[str] = []
    company_types: List[str] = []
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    max_jobs_per_search: int = 50
    min_match_score: int = 60
    sources: Dict[str, bool] = {"linkedin": True, "indeed": True}
    automation: Dict[str, bool] = {"auto_apply": False, "auto_discover": True}
    application_pace: str = "moderate"


class JobListingBase(BaseModel):
    title: str
    company: str
    company_logo: Optional[str] = None
    description: str
    url: HttpUrl
    source: JobSource
    external_id: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    is_remote: bool = False
    employment_type: Optional[str] = None


class JobListing(JobListingBase):
    id: str
    match_score: Optional[float] = None
    missing_skills: List[str] = []
    fit_analysis: Optional[str] = None
    recommended_keywords: List[str] = []
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class MatchResult(BaseModel):
    job_id: str
    match_score: float
    missing_skills: List[str]
    fit_analysis: str
    strengths: List[str]
    recommended_keywords: List[str]


class ResumeAnalysis(BaseModel):
    skills: List[str]
    experience_years: float
    job_titles: List[str]
    education: Optional[List[str]] = None
    certifications: Optional[List[str]] = None


class TailoredResume(BaseModel):
    original_id: Optional[str] = None
    tailored_text: str
    changes: Dict[str, Any]
    keywords_added: List[str]
    version: int = 1


class CoverLetterRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: str
    company: str
    tone: str = "professional"
    additional_points: Optional[str] = None


class CoverLetterResponse(BaseModel):
    cover_letter: str


class ATSAnalysis(BaseModel):
    ats_score: float
    issues: List[str]
    recommendations: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]


class QueueItem(BaseModel):
    id: str
    user_id: str
    job_id: str
    priority: str = "medium"
    position: int = 0
    status: str
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApplicationSubmission(BaseModel):
    queue_item_id: str
    user_id: str
    job_id: str
    tailored_resume_id: Optional[str] = None
    cover_letter: Optional[str] = None
    platform: str = "linkedin"


class DiscoveryRequest(BaseModel):
    user_id: str
    preferences: Optional[UserPreferences] = None
    job_titles: Optional[List[str]] = None
    location: Optional[str] = "Remote"
    max_jobs: Optional[int] = 50
    sources: Optional[List[str]] = ["linkedin", "indeed"]


class DiscoveryResponse(BaseModel):
    task_id: str
    status: str
    message: str
    jobs_found: Optional[int] = None
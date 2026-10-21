# backend/fastapi_app/routers/resumes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uuid

# ✅ Import Gemini Service
from ..services.gemini_service import GeminiService

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ Initialize Gemini Service
gemini_service = GeminiService()

# --- Request/Response Models ---

class TailorRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: str
    company: str
    resume_url: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_id: Optional[str] = None


class TailorResponse(BaseModel):
    resume_id: str
    tailored_text: str
    changes: Dict[str, Any]
    keywords_added: List[str]


class ATSCheckRequest(BaseModel):
    resume_text: str
    job_description: str


class ATSCheckResponse(BaseModel):
    ats_score: float
    issues: List[str]
    recommendations: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]


class ResumeAnalysisRequest(BaseModel):
    resume_text: str


class ResumeAnalysisResponse(BaseModel):
    skills: List[str]
    experience_years: float
    job_titles: List[str]
    education: Optional[List[str]] = None
    certifications: Optional[List[str]] = None


# --- Endpoints ---

import re

def _clean_tailored_text(text: str) -> str:
    """Remove markdown formatting and clean up the tailored text."""
    if not text:
        return text
    # Remove **bold** markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove *italic* markers  
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove __underline__ markers
    text = re.sub(r'__(.*?)__', r'\1', text)
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    # Clean up spaces before periods
    text = re.sub(r' \.', '.', text)
    return text.strip()


@router.post("/tailor", response_model=TailorResponse)
async def tailor_resume(request: TailorRequest):
    """Tailor resume for a specific job using Gemini AI"""
    try:
        logger.info(f"📝 Tailoring resume for: {request.job_title} at {request.company}")
        
        result = await gemini_service.tailor_resume(
            resume_text=request.resume_text,
            job_description=request.job_description,
            job_title=request.job_title,
            company=request.company,
            resume_url=request.resume_url
        )
        
        # Clean up any markdown formatting that Gemini might have added
        tailored_text = _clean_tailored_text(result.get("tailored_text", request.resume_text))
        
        return TailorResponse(
            resume_id=request.resume_id or str(uuid.uuid4()),
            tailored_text=tailored_text,
            changes=result.get("changes", {}),
            keywords_added=result.get("keywords_added", [])
        )
    except Exception as e:
        logger.error(f"❌ Resume tailoring error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats-check", response_model=ATSCheckResponse)
async def check_ats_compatibility(request: ATSCheckRequest):
    """Check resume ATS compatibility using Gemini AI"""
    try:
        logger.info("🔍 Checking ATS compatibility...")
        
        result = await gemini_service.check_ats_friendliness(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        
        return ATSCheckResponse(
            ats_score=result.get("ats_score", 50),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            matched_keywords=result.get("matched_keywords", []),
            missing_keywords=result.get("missing_keywords", [])
        )
    except Exception as e:
        logger.error(f"❌ ATS check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(request: ResumeAnalysisRequest):
    """Analyze resume and extract structured information using Gemini AI"""
    try:
        logger.info("🔍 Analyzing resume...")
        
        result = await gemini_service.extract_skills(request.resume_text)
        
        return ResumeAnalysisResponse(
            skills=result.get("skills", []),
            experience_years=result.get("experience_years", 0),
            job_titles=result.get("job_titles", []),
            education=None,
            certifications=None
        )
    except Exception as e:
        logger.error(f"❌ Resume analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_resumes_router():
    """Test endpoint to verify resumes router is working"""
    return {
        "status": "ok",
        "message": "Resumes router is working",
        "endpoints": [
            "POST /api/resumes/tailor",
            "POST /api/resumes/ats-check",
            "POST /api/resumes/analyze"
        ]
    }
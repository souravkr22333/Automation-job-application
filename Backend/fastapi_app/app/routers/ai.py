
# backend/fastapi_app/routers/ai.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# ✅ Import Gemini Service instead of OpenAI
from ..services.gemini_service import GeminiService

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ Initialize Gemini Service
gemini_service = GeminiService()

# --- Request/Response Models (Same as before) ---

class ExtractSkillsRequest(BaseModel):
    resume_text: str

class ExtractSkillsResponse(BaseModel):
    skills: List[str]
    experience_years: float
    job_titles: List[str]

class MatchRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: str
    company: str

class MatchResponse(BaseModel):
    match_score: float
    missing_skills: List[str]
    fit_analysis: str
    strengths: List[str]
    recommended_keywords: List[str]

class BatchMatchRequest(BaseModel):
    user_id: str
    resume_id: str
    resume_text: str
    job_ids: List[str]
    jobs: Optional[List[Dict[str, Any]]] = None

class TailorRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: str
    company: str
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_id: Optional[str] = None

class TailorResponse(BaseModel):
    resume_id: str
    tailored_text: str
    changes: Dict[str, Any]
    keywords_added: List[str]

class CoverLetterRequest(BaseModel):
    user_id: str
    job_id: str
    resume_text: str
    job_description: str
    job_title: str
    company: str
    tone: str = "professional"
    additional_points: str = ""

class CoverLetterResponse(BaseModel):
    cover_letter: str

class ATSCheckRequest(BaseModel):
    resume_text: str
    job_description: str

class ATSCheckResponse(BaseModel):
    ats_score: float
    issues: List[str]
    recommendations: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]


# --- Endpoints (Same but using Gemini) ---

@router.post("/extract-skills", response_model=ExtractSkillsResponse)
async def extract_skills(request: ExtractSkillsRequest):
    """Extract skills from resume text using Gemini AI"""
    try:
        result = await gemini_service.extract_skills(request.resume_text)
        return result
    except Exception as e:
        logger.error(f"Skill extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-match", response_model=MatchResponse)
async def calculate_match(request: MatchRequest):
    """Calculate match score between resume and job using Gemini AI"""
    try:
        result = await gemini_service.calculate_match(
            request.resume_text,
            request.job_description,
            request.job_title,
            request.company
        )
        return result
    except Exception as e:
        logger.error(f"Match calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-match")
async def batch_match(request: BatchMatchRequest):
    """
    Calculate match scores for multiple jobs using Gemini AI.
    Uses the same Gemini model (gemini-2.5-flash) as tailor_resume for consistency.
    """
    results = []
    
    # Build a lookup map from the jobs data sent directly from Django
    jobs_map = {}
    if request.jobs:
        for j in request.jobs:
            jobs_map[j.get('job_id')] = j
    
    for job_id in request.job_ids:
        job_data = jobs_map.get(job_id, {})
        
        if not job_data.get('description'):
            results.append({
                "job_id": job_id,
                "match_score": 0,
                "missing_skills": [],
                "fit_analysis": "No description available",
                "recommended_keywords": []
            })
            continue
        
        try:
            result = await gemini_service.calculate_match(
                request.resume_text,
                job_data.get('description', ''),
                job_data.get('title', ''),
                job_data.get('company', '')
            )
            # Ensure all expected fields exist
            results.append({
                "job_id": job_id,
                "match_score": result.get("match_score", 0),
                "missing_skills": result.get("missing_skills", []),
                "fit_analysis": result.get("fit_analysis", ""),
                "recommended_keywords": result.get("recommended_keywords", []),
                "strengths": result.get("strengths", [])
            })
        except Exception as e:
            logger.error(f"Match failed for job {job_id}: {str(e)}")
            results.append({
                "job_id": job_id,
                "match_score": 0,
                "missing_skills": [],
                "fit_analysis": f"Match calculation failed: {str(e)}",
                "recommended_keywords": []
            })
    
    return {
        "status": "success",
        "results": results
    }

@router.post("/tailor-resume", response_model=TailorResponse)
async def tailor_resume(request: TailorRequest):
    """Tailor resume for a specific job using Gemini AI"""
    try:
        result = await gemini_service.tailor_resume(
            request.resume_text,
            request.job_description,
            request.job_title,
            request.company
        )
        return result
    except Exception as e:
        logger.error(f"Resume tailoring failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(request: CoverLetterRequest):
    """Generate a cover letter using Gemini AI"""
    try:
        result = await gemini_service.generate_cover_letter(
            request.resume_text,
            request.job_description,
            request.job_title,
            request.company,
            request.tone,
            request.additional_points
        )
        return {"cover_letter": result}
    except Exception as e:
        logger.error(f"Cover letter generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ats-check", response_model=ATSCheckResponse)
async def ats_check(request: ATSCheckRequest):
    """Check resume ATS compatibility using Gemini AI"""
    try:
        result = await gemini_service.check_ats_friendliness(
            request.resume_text,
            request.job_description
        )
        return result
    except Exception as e:
        logger.error(f"ATS check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..services.job_scraper_service import JobScraperService

router = APIRouter()
logger = logging.getLogger(__name__)


class DiscoverJobsRequest(BaseModel):
    job_titles: List[str]
    location: str = "Remote"
    max_jobs: int = 50
    # kept for compatibility with existing frontend/django contract
    sources: List[str] = ["apify_linkedin"]
    days_back: int = 30


class SingleKeywordRequest(BaseModel):
    keyword: str
    location: str = "Remote"
    max_results: int = 20
    days_back: int = 30


class DebugRequest(BaseModel):
    actor_id: str
    keyword: str
    location: str = "Remote"
    max_results: int = 5


@router.post("/discover/linkedin")
async def discover_linkedin(request: SingleKeywordRequest):
    """Discover jobs from LinkedIn using Apify actor."""
    try:
        job_service = JobScraperService()
        jobs = job_service.discover_jobs(
            job_titles=[request.keyword],
            location=request.location,
            max_jobs=request.max_results,
            days_back=request.days_back,
        )

        return {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs": jobs,
            "source": "linkedin",
            "message": f"Found {len(jobs)} jobs from LinkedIn",
        }
    except Exception as e:
        logger.exception("LinkedIn scraping error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover/debug")
async def debug_scraper(request: DebugRequest):
    """Debug endpoint (kept for compatibility)."""
    try:
        job_service = JobScraperService(actor_id=request.actor_id)
        jobs = job_service.discover_jobs(
            job_titles=[request.keyword],
            location=request.location,
            max_jobs=request.max_results,
            days_back=30,
        )
        return {"status": "success", "data": {"actor_id": request.actor_id, "jobs": jobs}}
    except Exception as e:
        logger.exception("Debug error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover")
async def discover_jobs(request: DiscoverJobsRequest):
    """Multi-keyword discovery."""
    try:
        keywords = request.job_titles or []
        if not keywords:
            return {
                "status": "success",
                "jobs_found": 0,
                "jobs": [],
                "sources": request.sources,
                "message": "No job_titles provided",
            }

        job_service = JobScraperService()
        jobs = job_service.discover_jobs(
            job_titles=keywords,
            location=request.location,
            max_jobs=request.max_jobs,
            days_back=request.days_back,
        )

        return {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs": jobs,
            "sources": request.sources,
            "message": f"Found {len(jobs)} jobs",
        }
    except Exception as e:
        logger.exception("Job discovery error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def scraper_health():
    try:
        job_service = JobScraperService()
        configured = job_service.scraper.is_configured()
    except Exception:
        configured = False

    return {
        "status": "healthy" if configured else "degraded",
        "message": "Apify LinkedIn scraper ready",
        "configured": configured,
    }


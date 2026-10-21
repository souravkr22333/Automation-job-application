# backend/fastapi_app/tasks.py (add missing tasks)
import logging
from typing import List, Dict, Any
from celery import Task
from .celery_app import celery_app
from .services.job_scraper_service import JobScraperService
from .services.match_engine import MatchEngine
from .services.resume_tailor import ResumeTailor
from .services.openai_service import OpenAIService
from .submitters.platform_submitters import SubmitFactory
import httpx
import json
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name="submit_application")
def submit_application(queue_item_id: str, user_id: str, job_id: str, tailored_resume_id: str = None, cover_letter: str = "") -> Dict[str, Any]:
    """Submit an application to a job platform"""
    try:
        submit_factory = SubmitFactory()
        
        # Get job details
        response = httpx.get(
            f"http://django:8000/api/jobs/{job_id}/",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get job: {response.text}")
        
        job = response.json()
        
        # Get resume if tailored
        resume_content = ""
        if tailored_resume_id:
            response = httpx.get(
                f"http://django:8000/api/resumes/{tailored_resume_id}/",
                timeout=30
            )
            if response.status_code == 200:
                resume_content = response.json().get("parsed_text", "")
        
        # Submit application
        submitter = submit_factory.get_submitter(job.get("source"))
        result = submitter.submit(
            job_url=job.get("url"),
            resume=resume_content,
            cover_letter=cover_letter
        )
        
        # Update queue item status
        httpx.patch(
            f"http://django:8000/api/applications/queue/{queue_item_id}/",
            json={"status": "submitted", "submitted_at": result.get("timestamp")},
            timeout=30
        )
        
        return {
            "queue_item_id": queue_item_id,
            "status": "submitted",
            "result": result
        }
    except Exception as e:
        logger.error(f"Application submission error: {str(e)}")
        return {"queue_item_id": queue_item_id, "error": str(e)}


@celery_app.task(bind=True, max_retries=3, name="submit_application_bulk")
def submit_application_bulk(self, queue_item_id: str, user_id: str) -> Dict[str, Any]:
    """Submit a single application as part of bulk submission"""
    try:
        # Get queue item details from Django
        response = httpx.get(
            f"http://django:8000/api/applications/queue/{queue_item_id}/",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get queue item: {response.text}")
        
        item = response.json()
        
        # Submit the application
        return submit_application(
            queue_item_id=queue_item_id,
            user_id=user_id,
            job_id=item["job"],
            tailored_resume_id=item.get("tailored_resume"),
            cover_letter=item.get("cover_letter", "")
        )
    except Exception as e:
        logger.error(f"Bulk submission error for {queue_item_id}: {str(e)}")
        return {"queue_item_id": queue_item_id, "error": str(e)}


@celery_app.task(name="cancel_submission")
def cancel_submission(queue_item_id: str) -> Dict[str, Any]:
    """Cancel a pending submission"""
    try:
        # Update queue item status in Django
        response = httpx.patch(
            f"http://django:8000/api/applications/queue/{queue_item_id}/",
            json={"status": "paused"},
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to cancel submission: {response.text}")
        
        return {
            "queue_item_id": queue_item_id,
            "status": "cancelled"
        }
    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        return {"queue_item_id": queue_item_id, "error": str(e)}


@celery_app.task(name="generate_resume_analysis")
def generate_resume_analysis(resume_id: str, user_id: str) -> Dict[str, Any]:
    """Generate detailed analysis of a resume"""
    try:
        openai_service = OpenAIService()
        
        # Get resume from Django
        response = httpx.get(
            f"http://django:8000/api/resumes/{resume_id}/",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get resume: {response.text}")
        
        resume = response.json()
        resume_text = resume.get("parsed_text", "")
        
        # Analyze resume
        analysis = openai_service.extract_skills(resume_text)
        
        # Update resume with analysis
        httpx.patch(
            f"http://django:8000/api/resumes/{resume_id}/",
            json={
                "extracted_skills": analysis.get("skills", []),
                "extracted_experience": analysis.get("experience_years", 0),
                "extracted_job_titles": analysis.get("job_titles", [])
            },
            timeout=30
        )
        
        return {
            "resume_id": resume_id,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Resume analysis error: {str(e)}")
        return {"resume_id": resume_id, "error": str(e)}


@celery_app.task(name="sync_external_jobs")
def sync_external_jobs() -> Dict[str, Any]:
    """Sync jobs from external sources"""
    try:
        discovery_service = JobScraperService()
        
        # Get all active users with auto-discovery enabled
        response = httpx.get(
            "http://django:8000/api/users/",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get users: {response.text}")
        
        users = response.json()
        total_jobs = 0
        
        for user in users:
            preferences = user.get("preferences", {})
            if preferences.get("automation", {}).get("auto_discover", False):
                job_titles = preferences.get("job_titles", ["Software Engineer"])
                location = preferences.get("location", "Remote")
                
                # Discover jobs
                jobs = discovery_service.discover_jobs(
                    keywords=job_titles,
                    location=location,
                    sources=["linkedin", "indeed"],
                    max_results=50
                )
                
                # Store jobs
                for job in jobs:
                    httpx.post(
                        "http://django:8000/api/jobs/",
                        json={
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "description": job.get("description", ""),
                            "url": job.get("url"),
                            "source": job.get("source"),
                            "location": job.get("location", location)
                        },
                        timeout=30
                    )
                    total_jobs += 1
        
        return {
            "total_jobs": total_jobs,
            "users_processed": len(users)
        }
    except Exception as e:
        logger.error(f"External sync error: {str(e)}")
        return {"error": str(e)}
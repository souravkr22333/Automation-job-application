# backend/fastapi_app/routers/applications.py (add missing endpoints)
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import AnyHttpUrl, BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import secrets
import tempfile
from urllib.parse import urlparse

import httpx
from ..submitters.platform_submitters import SubmitFactory
from ..celery_app import celery_app
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
MAX_RESUME_SIZE = 10 * 1024 * 1024
RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}


class SubmitApplicationRequest(BaseModel):
    queue_item_id: Optional[str] = None
    user_data: Dict[str, Any]
    job: Dict[str, Any]
    resume_url: AnyHttpUrl
    cover_letter: str = ""
    platform: str = "unknown"


class SubmitApplicationResponse(BaseModel):
    status: str
    application_url: Optional[str] = None
    message: str


class BulkSubmitRequest(BaseModel):
    queue_item_ids: List[str]
    user_id: str


@router.post("/submit")
async def submit_application(
    request: SubmitApplicationRequest,
    x_internal_token: Optional[str] = Header(default=None),
):
    """Download the tailored resume and submit it through the configured platform flow."""
    configured_token = settings.AUTO_APPLY_INTERNAL_TOKEN
    if not configured_token:
        raise HTTPException(status_code=503, detail="Auto-apply service token is not configured")
    if not x_internal_token or not secrets.compare_digest(x_internal_token, configured_token):
        raise HTTPException(status_code=401, detail="Invalid internal service token")

    resume_path = None
    try:
        job_url = request.job.get("url")
        if not job_url:
            raise HTTPException(status_code=422, detail="Job URL is required")

        parsed_resume_url = urlparse(str(request.resume_url))
        extension = os.path.splitext(parsed_resume_url.path)[1].lower()
        if extension not in RESUME_EXTENSIONS:
            extension = ".pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as resume_file:
            resume_path = resume_file.name
            total_bytes = 0
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                async with client.stream("GET", str(request.resume_url)) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(64 * 1024):
                        total_bytes += len(chunk)
                        if total_bytes > MAX_RESUME_SIZE:
                            raise HTTPException(status_code=413, detail="Resume exceeds 10 MB")
                        resume_file.write(chunk)
            if total_bytes == 0:
                raise HTTPException(status_code=422, detail="Downloaded resume is empty")

        submitter = SubmitFactory.get_submitter(request.platform)
        result = await submitter.submit_application(
            user_data=request.user_data,
            job=request.job,
            resume_path=resume_path,
            cover_letter=request.cover_letter,
            platform=request.platform,
        )

        if result.get("status") == "success":
            return {
                "status": "success",
                "application_url": result.get("application_url"),
                "message": result.get("message", "Application submitted successfully"),
            }
        if result.get("status") == "pending":
            return {
                "status": "pending_confirmation",
                "application_url": result.get("application_url"),
                "message": result.get("message", "Submission was attempted but could not be confirmed"),
            }

        logger.warning(
            "Application submission failed for queue item %s: %s",
            request.queue_item_id,
            result.get("reason", "Unknown submission error"),
        )
        raise HTTPException(
            status_code=422,
            detail=result.get("reason", "Application submission failed"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Submission error for queue item %s", request.queue_item_id)
        raise HTTPException(status_code=502, detail="Unable to submit application") from e
    finally:
        if resume_path and os.path.exists(resume_path):
            try:
                os.unlink(resume_path)
            except OSError:
                logger.exception("Failed to remove temporary resume file %s", resume_path)

@router.post("/bulk-submit", response_model=Dict[str, Any])
async def bulk_submit_applications(request: BulkSubmitRequest, background_tasks: BackgroundTasks):
    """Submit multiple applications in bulk"""
    try:
        task_ids = []
        for queue_item_id in request.queue_item_ids:
            task = celery_app.send_task(
                "submit_application_bulk",
                args=[queue_item_id, request.user_id]
            )
            task_ids.append(task.id)
        
        return {
            "status": "queued",
            "task_ids": task_ids,
            "count": len(task_ids),
            "message": f"Bulk submission started for {len(task_ids)} applications"
        }
    except Exception as e:
        logger.error(f"Bulk submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_submission_status(task_id: str):
    """Get submission task status"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{queue_item_id}")
async def retry_submission(queue_item_id: str):
    """Retry a failed submission"""
    try:
        task = celery_app.send_task(
            "retry_submission",
            args=[queue_item_id]
        )
        return {
            "task_id": task.id,
            "message": "Retry submitted"
        }
    except Exception as e:
        logger.error(f"Retry error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{queue_item_id}")
async def cancel_submission(queue_item_id: str):
    """Cancel a pending submission"""
    try:
        task = celery_app.send_task(
            "cancel_submission",
            args=[queue_item_id]
        )
        return {
            "task_id": task.id,
            "message": "Cancellation submitted"
        }
    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
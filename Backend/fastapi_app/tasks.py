import logging
from typing import Any, Dict

from .celery_app import celery_app

logger = logging.getLogger(__name__)


# Job scraping + external job discovery removed.
# This file previously contained Celery tasks that depended on
# app.services.job_discovery and FastAPI job scraping routes.


@celery_app.task(name="submit_application")
def submit_application(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Placeholder: submit application task body removed with job scraping dependencies."""
    return {"status": "removed", "args": list(args), "kwargs": kwargs}


import logging
from typing import Any, Dict, List

from ..scrapers.apify_linkedin_scraper import ApifyLinkedInJobScraper

logger = logging.getLogger(__name__)


class JobScraperService:
    def __init__(self, actor_id: str | None = None):
        self.scraper = ApifyLinkedInJobScraper(actor_id=actor_id)

    def discover_jobs(
        self,
        job_titles: List[str],
        location: str = "Remote",
        max_jobs: int = 50,
        days_back: int = 30,
    ) -> List[Dict[str, Any]]:
        if not job_titles:
            return []

        # Apify actor expects one keyword string; pass as list and let scraper build query.
        jobs = self.scraper.search_jobs(
            keywords=job_titles,
            location=location,
            max_results=max_jobs,
            days_back=days_back,
        )

        # Ensure result count
        return jobs[:max_jobs]


# backend/fastapi_app/app/scrapers/apify_linkedin_scraper.py
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from apify_client import ApifyClient

from ..config import settings

logger = logging.getLogger(__name__)


class ApifyLinkedInJobScraper:
    """Apify-based LinkedIn jobs scraper."""

    def __init__(self, actor_id: Optional[str] = None):
        self.api_token = settings.APIFY_API_TOKEN
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN not set in environment variables")
        
        self.client = ApifyClient(self.api_token) if self.api_token else None
        self.actor_id = actor_id or getattr(settings, 'APIFY_DEFAULT_ACTOR', 'curious_coder~linkedin-jobs-scraper')

    def is_configured(self) -> bool:
        """Check if Apify is properly configured."""
        if not self.client:
            return False
        try:
            self.client.actor(self.actor_id).get()
            return True
        except Exception as e:
            logger.error(f"Apify actor not configured: {str(e)}")
            return False

    def search_jobs(
        self,
        keywords: List[str],
        location: str = "Remote",
        max_results: int = 50,
        days_back: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn using Apify.
        """
        if not self.is_configured():
            logger.error("Apify is not configured. Please set APIFY_API_TOKEN.")
            return []

        try:
            # Build search URL
            date_posted = self._days_back_to_date_posted(days_back)
            encoded_keywords = " OR ".join([k.strip() for k in keywords if k and k.strip()])
            
            search_url = (
                "https://www.linkedin.com/jobs/search?"
                f"keywords={quote(encoded_keywords)}"
                + (f"&location={quote(location)}" if location else "")
            )

            # Build actor input
            actor_input = {
                "searchKeywords": encoded_keywords,
                "location": location,
                "maxItems": max_results,
                "datePosted": date_posted,
                "urls": [search_url],
                "count": max_results,
                "scrapeCompany": True,
                "splitByLocation": False,
                "splitCountry": "IN",
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            }

            logger.info(f"Running Apify Actor: {self.actor_id}")
            logger.info(f"Search URL: {search_url}")
            logger.info(f"Max Results: {max_results}")

            # Run the actor - this returns a typed Run object
            run = self.client.actor(self.actor_id).call(
                run_input=actor_input,
            )

            # Check if run is None
            if run is None:
                logger.error("Actor run failed - returned None")
                return []

            # Access dataset ID using dot notation (typed Run object)
            # According to Apify AI, use run.default_dataset_id (dot notation)
            dataset_id = None
            try:
                # Method 1: Dot notation (recommended by Apify AI)
                dataset_id = run.default_dataset_id
                logger.info(f"Dataset ID from dot notation: {dataset_id}")
            except AttributeError:
                # Fallback: try dictionary-style access
                try:
                    dataset_id = run.get('defaultDatasetId')
                    logger.info(f"Dataset ID from dict access: {dataset_id}")
                except AttributeError:
                    # Try to get from run dict if it's a dict
                    try:
                        if hasattr(run, '__getitem__'):
                            dataset_id = run['defaultDatasetId']
                            logger.info(f"Dataset ID from __getitem__: {dataset_id}")
                    except (KeyError, TypeError):
                        pass

            # If we have a dataset ID, fetch the items
            if dataset_id:
                logger.info(f"Using dataset_id: {dataset_id}")
                dataset = self.client.dataset(dataset_id)
                
                # Get items from dataset
                items = []
                try:
                    # Method 1: list_items (recommended by Apify AI)
                    dataset_items = dataset.list_items()
                    if dataset_items and hasattr(dataset_items, 'items'):
                        items = dataset_items.items
                    elif dataset_items and isinstance(dataset_items, dict):
                        items = dataset_items.get('items', [])
                except Exception as e:
                    logger.warning(f"list_items failed: {str(e)}")
                    # Method 2: iterate_items
                    try:
                        items = list(dataset.iterate_items(limit=1000))
                    except Exception as e2:
                        logger.warning(f"iterate_items failed: {str(e2)}")
                        # Method 3: get_items
                        try:
                            response = dataset.get_items()
                            if isinstance(response, dict):
                                items = response.get('items', [])
                            elif isinstance(response, list):
                                items = response
                        except Exception as e3:
                            logger.error(f"All dataset fetch methods failed: {str(e3)}")
                
                if items:
                    logger.info(f"Fetched {len(items)} items from dataset")
                    results = [self._normalize_job(item) for item in items]
                    logger.info(f"Apify returned {len(results)} jobs")
                    return results
                else:
                    logger.warning(f"No items found in dataset {dataset_id}")

            # Fallback: Try to get items directly using the run ID as dataset ID
            logger.info("Trying to get items using run ID as dataset ID...")
            try:
                run_id = run.id if hasattr(run, 'id') else None
                if run_id:
                    dataset = self.client.dataset(run_id)
                    items = list(dataset.iterate_items(limit=1000))
                    if items:
                        logger.info(f"Fetched {len(items)} items using run_id as dataset_id")
                        results = [self._normalize_job(item) for item in items]
                        return results
            except Exception as e:
                logger.warning(f"Failed to get items using run_id: {str(e)}")

            # Last resort: Try to get items from run output
            logger.info("Trying to extract items from run output...")
            items = self._extract_items_from_run(run)
            if items:
                results = [self._normalize_job(item) for item in items]
                logger.info(f"Apify returned {len(results)} jobs from run output")
                return results

            logger.error("No jobs found from Apify run")
            return []

        except Exception as e:
            logger.error(f"Apify job search failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _extract_items_from_run(self, run: Any) -> List[Dict[str, Any]]:
        """
        Extract items directly from run output when dataset is not accessible.
        """
        try:
            # Try to get run as dict
            run_dict = None
            try:
                if hasattr(run, '__dict__'):
                    run_dict = run.__dict__
                elif isinstance(run, dict):
                    run_dict = run
            except Exception:
                pass

            if not run_dict:
                return []

            # Helper to extract items from various formats
            def extract_items(obj: Any) -> Optional[List[Any]]:
                if obj is None:
                    return None
                if isinstance(obj, list):
                    return obj
                if isinstance(obj, dict):
                    # Common keys where items might be stored
                    for key in ['items', 'results', 'output', 'outputData', 'scrapedItems', 'jobs', 'data']:
                        if key in obj and obj.get(key) is not None:
                            val = obj.get(key)
                            if isinstance(val, list):
                                return val
                    # Check nested in meta
                    meta = obj.get('meta', {})
                    if isinstance(meta, dict):
                        for key in ['items', 'results', 'output']:
                            if key in meta and isinstance(meta.get(key), list):
                                return meta.get(key)
                    # Check nested in data
                    data = obj.get('data', {})
                    if isinstance(data, dict):
                        for key in ['items', 'results']:
                            if key in data and isinstance(data.get(key), list):
                                return data.get(key)
                return None

            items = extract_items(run_dict)
            
            if items:
                logger.info(f"Extracted {len(items)} items directly from run output")
                return [item for item in items if isinstance(item, dict)]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to extract items from run: {str(e)}")
            return []

    def _days_back_to_date_posted(self, days_back: int) -> Optional[str]:
        """Convert days back to LinkedIn date posted filter."""
        if not days_back:
            return None
        if days_back <= 1:
            return "past24hours"
        if days_back <= 7:
            return "pastWeek"
        if days_back <= 30:
            return "pastMonth"
        return "any-time"

    def _normalize_job(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data to consistent schema."""
        
        def safe_get(keys: List[str]) -> Optional[str]:
            for k in keys:
                v = item.get(k)
                if v and str(v).strip():
                    return str(v).strip()
            return None

        def extract_salary(field: str) -> Optional[float]:
            salary_data = item.get("salary") or item.get("salaryRange") or item.get("compensation") or {}
            # Your sample provides salary as a string like "$110,000.00/yr - $160,000.00/yr"
            if isinstance(salary_data, str):
                text = salary_data.replace(',', '')
                # Try to parse simple patterns for min/max
                if field == "min":
                    import re
                    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/yr|/yr\b)?\s*[-–]", text)
                    if m:
                        try:
                            return float(m.group(1))
                        except Exception:
                            return None
                if field == "max":
                    import re
                    m = re.search(r"[-–]\s*\$\s*([0-9]+(?:\.[0-9]+)?)", text)
                    if m:
                        try:
                            return float(m.group(1))
                        except Exception:
                            return None
                if field == "currency":
                    return "USD"
                return None
            if isinstance(salary_data, dict):
                if field == "min":
                    val = salary_data.get("min") or salary_data.get("minimum") or salary_data.get("from")
                elif field == "max":
                    val = salary_data.get("max") or salary_data.get("maximum") or salary_data.get("to")
                elif field == "currency":
                    return salary_data.get("currency") or salary_data.get("currencyCode")
                else:
                    return None
                try:
                    return float(val) if val else None
                except (ValueError, TypeError):
                    return None
            return None

        # Extract location and remote status
        location = safe_get(["location", "jobLocation", "job_location"]) or ""
        
        is_remote = False
        remote_fields = ["remote", "isRemote", "workType", "workplaceType"]
        for rf in remote_fields:
            v = item.get(rf)
            if isinstance(v, bool):
                is_remote = v
                break
            if isinstance(v, str) and v.lower() in ["remote", "yes", "true", "1", "fully remote"]:
                is_remote = True
                break
        if not is_remote and "remote" in location.lower():
            is_remote = True

        # Extract URL
        url = safe_get([
            "url", "jobUrl", "jobURL", "job_url", 
            "jobLink", "job_link", "link", 
            "applyUrl", "apply_url", "apply"
        ]) or ""

            # Build job object
        job = {
            "title": safe_get(["title", "jobTitle", "job_title", "position"]) or "",
            "company": safe_get(["company", "companyName", "company_name", "companyName_text"]) or "",
            "url": url,
            "jobUrl": url,
            "company_logo": safe_get(["companyLogo", "company_logo", "logoUrl", "companyLogoUrl"]),
            "company_website": safe_get(["companyWebsite", "company_website"]),
            "company_industry": safe_get(["companyIndustry", "industry"]),
            "company_slogan": safe_get(["companySlogan", "company_slogan"]),
            "company_description": safe_get(["companyDescription", "company_description"]),
            # Django expects `employees_count`.
            # Keep `company_employees_count` too for backward compatibility with any other consumers.
            "employees_count": safe_get([
                "employees_count",
                "employeesCount",
                "companyEmployeesCount",
                "company_employees_count",
            ]),
            "company_employees_count": safe_get([
                "companyEmployeesCount",
                "company_employees_count",
                "employeesCount",
                "employees_count",
            ]),
            "company_linkedin_url": safe_get(["companyLinkedinUrl", "company_linkedin_url"]),
            "company_logo_url": safe_get(["companyLogo", "company_logo_url", "company_logo"]),


            "location": location,
            # Apify dataset provides: descriptionText (and sometimes descriptionHtml)
            "description": (
                safe_get([
                    "description",
                    "descriptionText",
                    "jobDescription",
                    "job_description",
                    "text",
                ]) or ""
            ),
            "source": "linkedin",
            "external_id": safe_get(["id", "jobId", "job_id", "listingId"]),
            "posted_date": safe_get(["postedAt", "postedDate", "posted_date", "datePosted"]),
            # Salary in your sample is a string, not a dict with min/max
            "salary": safe_get(["salary", "salaryText", "compensation"] ) or "",
            "salary_min": extract_salary("min"),
            "salary_max": extract_salary("max"),
            "salary_currency": extract_salary("currency") or "USD",
            "employment_type": safe_get(["employmentType", "jobType", "employment_type"]),
            "experience_level": safe_get(["experienceLevel", "experience_level", "seniorityLevel"]),
            "is_remote": is_remote,
            "apply_url": safe_get(["applyUrl", "apply_url", "applicationUrl", "inputUrl"]) or url,
        }

        # Clean up null/empty values
        return {k: v for k, v in job.items() if v is not None}

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a run."""
        try:
            run = self.client.run(run_id).get()
            if hasattr(run, '__dict__'):
                return {
                    'run_id': run_id,
                    'status': getattr(run, 'status', None),
                    'progress': getattr(run, 'progress', 0),
                    'started_at': getattr(run, 'startedAt', None),
                    'finished_at': getattr(run, 'finishedAt', None),
                    'dataset_id': getattr(run, 'default_dataset_id', None)
                }
            elif isinstance(run, dict):
                return {
                    'run_id': run_id,
                    'status': run.get('status'),
                    'progress': run.get('progress', 0),
                    'started_at': run.get('startedAt'),
                    'finished_at': run.get('finishedAt'),
                    'dataset_id': run.get('defaultDatasetId')
                }
            return {'run_id': run_id, 'error': 'Invalid run response'}
        except Exception as e:
            return {'run_id': run_id, 'error': str(e)}

    def get_run_results(self, run_id: str) -> List[Dict[str, Any]]:
        """Get results from a completed run by run_id."""
        try:
            # Get run details
            run = self.client.run(run_id).get()
            
            # Get dataset ID using dot notation
            dataset_id = None
            try:
                dataset_id = run.default_dataset_id
            except AttributeError:
                try:
                    dataset_id = run.get('defaultDatasetId')
                except AttributeError:
                    pass
            
            if dataset_id:
                dataset = self.client.dataset(dataset_id)
                items = list(dataset.iterate_items(limit=1000))
                if items:
                    return [self._normalize_job(item) for item in items]
            
            # Try using run_id as dataset_id
            try:
                dataset = self.client.dataset(run_id)
                items = list(dataset.iterate_items(limit=1000))
                if items:
                    return [self._normalize_job(item) for item in items]
            except Exception:
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get run results: {str(e)}")
            return []
# backend/fastapi_app/services/apify_monitor.py
import logging
from apify_client import ApifyClient
from ..config import settings

logger = logging.getLogger(__name__)

class ApifyMonitor:
    """Monitor Apify actor runs"""
    
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_API_TOKEN)
    
    def get_run_status(self, run_id: str):
        """Get status of a specific run"""
        try:
            run = self.client.run(run_id).get()
            return {
                "id": run.get("id"),
                "status": run.get("status"),
                "started_at": run.get("startedAt"),
                "finished_at": run.get("finishedAt"),
                "dataset_id": run.get("defaultDatasetId"),
                "items_count": run.get("itemsCount", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get run status: {str(e)}")
            return None
    
    def list_recent_runs(self, actor_id: str, limit: int = 10):
        """List recent runs for an actor"""
        try:
            runs = self.client.actor(actor_id).runs().list(limit=limit)
            return [{
                "id": run.get("id"),
                "status": run.get("status"),
                "started_at": run.get("startedAt"),
                "items_count": run.get("itemsCount", 0)
            } for run in runs.items]
        except Exception as e:
            logger.error(f"Failed to list runs: {str(e)}")
            return []
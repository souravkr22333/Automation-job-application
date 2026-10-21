# backend/fastapi_app/services/match_engine.py
import logging
from typing import List, Dict, Any
from .openai_service import OpenAIService

logger = logging.getLogger(__name__)

class MatchEngine:
    """Match engine for job-resume matching"""
    
    def __init__(self):
        self.openai = OpenAIService()
    
    async def calculate_match(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """Calculate match score between resume and job"""
        return await self.openai.calculate_match(
            resume_text,
            job_description,
            job_title,
            company
        )
    
    async def batch_calculate(
        self,
        resume_text: str,
        jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate match scores for multiple jobs"""
        results = []
        
        for job in jobs:
            try:
                result = await self.calculate_match(
                    resume_text,
                    job.get('description', ''),
                    job.get('title', 'Unknown'),
                    job.get('company', 'Unknown')
                )
                
                results.append({
                    'job_id': job.get('id'),
                    **result
                })
            except Exception as e:
                logger.error(f"Error matching job {job.get('id')}: {str(e)}")
                results.append({
                    'job_id': job.get('id'),
                    'error': str(e)
                })
        
        return results
    
    async def rank_jobs(
        self,
        resume_text: str,
        jobs: List[Dict[str, Any]],
        min_score: int = 60,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Rank jobs by match score"""
        results = await self.batch_calculate(resume_text, jobs)
        
        # Filter and sort
        filtered = [
            r for r in results 
            if r.get('match_score', 0) >= min_score
        ]
        
        sorted_results = sorted(
            filtered,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )
        
        return sorted_results[:max_results]
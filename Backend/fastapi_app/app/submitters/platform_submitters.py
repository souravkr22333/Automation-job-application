# backend/fastapi_app/submitters/platform_submitters.py
from typing import Dict, Any
from .playwright_submitter import ApplicationSubmitter


class LinkedInSubmitter(ApplicationSubmitter):
    """LinkedIn-specific application submitter"""
    
    def __init__(self):
        super().__init__()
    
    async def submit(self, user_data: Dict[str, Any], job: Dict[str, Any], 
                     resume_path: str, cover_letter: str) -> Dict[str, Any]:
        """Submit application via LinkedIn"""
        # LinkedIn Easy Apply flow
        return await self.submit_application(
            user_data=user_data,
            job=job,
            resume_path=resume_path,
            cover_letter=cover_letter,
            platform="linkedin"
        )


class IndeedSubmitter(ApplicationSubmitter):
    """Indeed-specific application submitter"""
    
    def __init__(self):
        super().__init__()
    
    async def submit(self, user_data: Dict[str, Any], job: Dict[str, Any],
                     resume_path: str, cover_letter: str) -> Dict[str, Any]:
        """Submit application via Indeed"""
        return await self.submit_application(
            user_data=user_data,
            job=job,
            resume_path=resume_path,
            cover_letter=cover_letter,
            platform="indeed"
        )


class GlassdoorSubmitter(ApplicationSubmitter):
    """Glassdoor-specific application submitter"""
    
    def __init__(self):
        super().__init__()
    
    async def submit(self, user_data: Dict[str, Any], job: Dict[str, Any],
                     resume_path: str, cover_letter: str) -> Dict[str, Any]:
        """Submit application via Glassdoor"""
        return await self.submit_application(
            user_data=user_data,
            job=job,
            resume_path=resume_path,
            cover_letter=cover_letter,
            platform="glassdoor"
        )


class SubmitFactory:
    """Factory for platform-specific submitters"""
    
    @staticmethod
    def get_submitter(source: str) -> ApplicationSubmitter:
        """Get the appropriate submitter for the platform"""
        submitters = {
            "linkedin": LinkedInSubmitter,
            "indeed": IndeedSubmitter,
            "glassdoor": GlassdoorSubmitter,
        }
        
        submitter_class = submitters.get(source.lower())
        if submitter_class:
            return submitter_class()
        
        # Default to generic submitter
        return ApplicationSubmitter()
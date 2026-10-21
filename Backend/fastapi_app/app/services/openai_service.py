# backend/fastapi_app/services/openai_service.py
import openai
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def extract_skills(self, resume_text: str) -> Dict[str, Any]:
        """Extract skills, experience, and job titles from resume"""
        prompt = f"""
        Analyze this resume and extract structured information.
        
        RESUME:
        {resume_text[:4000]}
        
        Extract and return as JSON:
        1. skills: List of technical and soft skills (10-20 items)
        2. experience_years: Total years of professional experience (numeric)
        3. job_titles: List of job titles from career history
        
        Return ONLY valid JSON.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract structured information from resumes. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Ensure all fields exist
            return {
                "skills": result.get("skills", []),
                "experience_years": result.get("experience_years", 0),
                "job_titles": result.get("job_titles", [])
            }
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            raise
    
    async def calculate_match(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """Calculate match score between resume and job"""
        prompt = f"""
        Analyze how well this candidate matches the job.
        
        JOB: {job_title} at {company}
        JOB DESCRIPTION:
        {job_description[:2000]}
        
        RESUME:
        {resume_text[:2000]}
        
        Return as JSON:
        1. match_score: Overall match score (0-100)
        2. missing_skills: Top 5 skills from job description missing from resume
        3. fit_analysis: 2-3 sentence analysis of the fit
        4. strengths: Top 5 strengths the candidate brings
        5. recommended_keywords: 5 keywords to add to improve ATS match
        
        Return ONLY valid JSON.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert job matching analyst. Provide detailed match analysis. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return {
                "match_score": result.get("match_score", 0),
                "missing_skills": result.get("missing_skills", []),
                "fit_analysis": result.get("fit_analysis", ""),
                "strengths": result.get("strengths", []),
                "recommended_keywords": result.get("recommended_keywords", [])
            }
        except Exception as e:
            logger.error(f"Error calculating match: {str(e)}")
            raise
    
    async def generate_cover_letter(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str,
        tone: str = "professional",
        additional_points: str = ""
    ) -> str:
        """Generate a tailored cover letter"""
        tone_descriptions = {
            "professional": "formal and professional",
            "enthusiastic": "enthusiastic and passionate",
            "concise": "concise and direct",
            "casual": "friendly and casual"
        }
        
        tone_desc = tone_descriptions.get(tone, "professional")
        
        prompt = f"""
        Write a professional cover letter for this job application.
        
        JOB: {job_title} at {company}
        JOB DESCRIPTION:
        {job_description[:1500]}
        
        RESUME:
        {resume_text[:1500]}
        
        TONE: {tone_desc}
        ADDITIONAL POINTS: {additional_points if additional_points else "None"}
        
        Requirements:
        1. 3-4 paragraphs, 250-300 words
        2. Highlight relevant skills and experience
        3. Show enthusiasm for the role and company
        4. Professional format with proper salutation and closing
        5. No placeholders - use actual information from the resume
        
        Return the cover letter as plain text.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Write professional cover letters. Return only the cover letter text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise
    
    async def analyze(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Generic analysis endpoint with JSON response"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt or "You are an expert analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            raise
# backend/fastapi_app/services/gemini_service.py
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(env_path)

from ..config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Google Gemini AI Service - Free replacement for OpenAI
    """

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')

        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not set. Get it from https://aistudio.google.com/")
            logger.warning("⚠️ Using mock responses for testing")
            self.mock_mode = True
        else:
            self.mock_mode = False
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"🔧 GeminiService initialized with model: {self.model_name}")

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response from Gemini"""
        if self.mock_mode:
            logger.warning("⚠️ Using mock response (no API key)")
            return self._get_mock_response(prompt)

        try:
            full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"❌ Gemini error: {str(e)}")
            raise

    async def generate_json_response(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Generate a JSON response from Gemini"""
        if self.mock_mode:
            logger.warning("⚠️ Using mock JSON response (no API key)")
            return self._get_mock_json_response(prompt)

        try:
            json_instruction = "\n\nReturn ONLY valid JSON. Do not include any other text."
            full_prompt = (system_prompt or "") + "\n" + prompt + json_instruction

            response = self.model.generate_content(full_prompt)

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {str(e)}")
            return self._get_mock_json_response(prompt)
        except Exception as e:
            logger.error(f"❌ Gemini error: {str(e)}")
            return self._get_mock_json_response(prompt)

    # ========== MOCK RESPONSES (For testing without API key) ==========

    def _get_mock_response(self, prompt: str) -> str:
        """Return mock response for testing"""
        return "This is a mock response from Gemini. Please set GEMINI_API_KEY for real responses."

    def _get_mock_json_response(self, prompt: str) -> Dict[str, Any]:
        """Return mock JSON response for testing"""
        if "extract" in prompt.lower() or "skills" in prompt.lower():
            return {
                "skills": ["Python", "React", "Django", "PostgreSQL", "AWS"],
                "experience_years": 5,
                "job_titles": ["Software Engineer", "Senior Developer"]
            }
        elif "match" in prompt.lower():
            return {
                "match_score": 85,
                "missing_skills": ["TypeScript", "GraphQL"],
                "fit_analysis": "Strong match with some skill gaps.",
                "strengths": ["React expertise", "Leadership"],
                "recommended_keywords": ["TypeScript", "AWS", "GraphQL"]
            }
        elif "tailor" in prompt.lower():
            return {
                "tailored_text": "This is a tailored resume for the specific job.",
                "changes": {"added": ["TypeScript"], "reordered": ["Experience"]},
                "keywords_added": ["TypeScript", "AWS"]
            }
        else:
            return {"message": "Mock response"}

    # ========== REAL METHODS ==========

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
        """
        system_prompt = "You are an expert resume parser. Extract structured information from resumes."
        return await self.generate_json_response(prompt, system_prompt)

    async def calculate_match(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """
        Calculate match score between resume and job.
        Uses same Gemini model (gemini-2.5-flash) as tailor_resume for consistency.
        """
        prompt = f"""
        You are an expert job matching analyst. Analyze how well this candidate matches the job.
        Provide deep, meaningful analysis that considers both explicit skills and transferable experience.

        JOB POSITION: {job_title}
        COMPANY: {company}
        
        JOB DESCRIPTION:
        {job_description[:3000]}

        CANDIDATE RESUME:
        {resume_text[:3000]}

        Provide detailed analysis and return as JSON with these exact fields:
        1. match_score: Overall match percentage (0-100). Be realistic: 85+ for excellent matches, 60-84 for good matches, below 60 for partial matches
        2. missing_skills: Top 3-5 most important skills from the job description that are missing from the resume
        3. fit_analysis: 2-3 sentences explaining overall fit. Be specific about strengths and gaps
        4. strengths: Top 3-5 strongest qualifications/experiences the candidate brings for this role
        5. recommended_keywords: 5 keywords/skills to add to resume to improve match and ATS scoring

        CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no extra text.
        """
        system_prompt = "You are an expert job matching analyst. Provide detailed, realistic match analysis."
        return await self.generate_json_response(prompt, system_prompt)

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
        system_prompt = "You are an expert resume writer. Write professional cover letters. Return only the cover letter text."
        return await self.generate_response(prompt, system_prompt)

    async def tailor_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str,
        resume_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job"""
        format_instruction = ""
        if resume_url:
            format_instruction = """

        IMPORTANT - PRESERVE ALL SECTIONS:
        The tailored version MUST contain ALL sections from the original resume.
        Do NOT remove any section. However, REORDER sections for best presentation:
        - Put PROJECTS section in the MIDDLE (after Skills, before Education/Certificates)
        - Convert ALL content into bullet points for readability
        - Use natural human-sounding language
        """

        prompt = f"""
        You are an expert resume writer who creates beautifully formatted, human-sounding resumes.
        Tailor this resume for the job with natural, flowing language.

        JOB: {job_title} at {company}
        JOB DESCRIPTION:
        {job_description[:3000]}

        ORIGINAL RESUME:
        {resume_text[:6000]}

        {format_instruction}

        CRITICAL FORMATTING RULES:
        1. PRESERVE ALL sections AND ALL content from the original resume - do not remove anything
        2. REORDER sections in this exact order:
           a. SUMMARY: (write as 2-3 concise, human-sounding sentences - not bullet points)
           b. SKILLS: (each skill category on its own line with bullet points)
           c. EXPERIENCE: (most relevant first, bullet points for responsibilities)
           d. PROJECTS: (in middle, with bullet points)
           e. EDUCATION: (bullet points for each entry)
           f. CERTIFICATIONS: (bullet points)
           g. ADDITIONAL: (if exists, bullet points)

        3. SECTION HEADERS: Use the exact format "HEADER:" followed by content on next lines.
           Examples: "SUMMARY:", "SKILLS:", "EXPERIENCE:", "PROJECTS:", "EDUCATION:", "CERTIFICATIONS:"
           This is REQUIRED so the PDF generator can detect and bold them.

        4. BULLET POINT USAGE (ALL sections except SUMMARY use bullet points):
           - SKILLS: KEEP IT CONCISE - just list factual skills without any extra commentary or fluff.
             Each category as "- Category: skill1, skill2, skill3"
             GOOD example: "- Languages: Python, JavaScript, TypeScript"
             BAD example: "- Languages: Python, JavaScript. Eager to learn new languages..."
             Do NOT add phrases like "eager to learn", "quick learner", "passionate about".
             Just list the skills factually with no fluff.
           - EDUCATION: Each entry as "- Degree, Institution | Year"
           - EXPERIENCE: Each responsibility as "- action verb + description + metric"
           - PROJECTS: Each project should have its PROJECT NAME ON ITS OWN LINE IN ALL CAPS followed by colon so it stands out clearly as a sub-heading. Then 3-5 bullet points with details below.
             EXAMPLE FORMAT:
             "AI-POWERED COLLEGE PREDICTION:
             - Built full-stack app using Python, Django, Next.js with ML integration
             - Designed responsive UI for intuitive user experience
             - Engineered REST APIs supporting scalable data processing
             - Achieved 85% prediction accuracy using machine learning models"
           - CERTIFICATIONS: Each cert as "- Certification Name"

        5. HUMANIZED NATURAL LANGUAGE:
           - Write in natural, flowing English - avoid robotic or keyword-stuffed sentences
           - Use action verbs (developed, designed, implemented, led, optimized, built, created)
           - Sound like a real person wrote it, not an AI
           - Vary sentence structure naturally
           - Avoid repetitive phrasing
           - Keep it professional but conversational and authentic
           - Each bullet point should read naturally, not like a keyword list

        6. DO NOT use markdown, **bold**, *italic*, or any special formatting
        7. Keep all factual information accurate - do not fabricate
        8. Keep total length reasonable for a one-page resume

        Return as JSON:
        1. tailored_text: The complete tailored resume with ALL sections preserved, reordered correctly, using colon-based section headers, bullet points for skills/education/projects/experience, and humanized natural language
        2. changes: Summary of changes made (object with added, removed, modified, reordered sections)
        3. keywords_added: List of keywords added from job description
        """
        system_prompt = "You are an expert resume writer who creates ATS-optimized resumes that sound natural and human. You use colon-based section headers. You convert skills, education, projects, and experience into bullet points. You never use markdown. You write in natural, flowing English with action verbs."
        return await self.generate_json_response(prompt, system_prompt)

    async def check_ats_friendliness(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        """Check resume for ATS compatibility"""
        prompt = f"""
        Analyze this resume for ATS (Applicant Tracking System) compatibility.

        RESUME:
        {resume_text[:3000]}

        JOB DESCRIPTION (for context):
        {job_description[:1500]}

        Analyze the resume for:
        1. Keyword density and relevance
        2. Formatting issues
        3. Section headers and structure
        4. File format compatibility
        5. Quantifiable achievements

        Return as JSON:
        1. ats_score: ATS compatibility score (0-100)
        2. issues_found: List of issues found
        3. recommendations: List of recommendations to improve
        4. keyword_matches: Keywords from job description found in resume
        5. missing_keywords: Keywords from job description missing from resume
        """
        system_prompt = "You are an expert ATS optimization specialist. Analyze resumes for ATS compatibility."
        return await self.generate_json_response(prompt, system_prompt)

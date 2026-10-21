# backend/django_app/resumes/tasks.py
import logging
import json
import os
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import Resume, ResumeVersion
from .services import ResumeParser, ResumeStorageService
from core.supabase_client import supabase_client
import httpx

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def parse_resume_async(self, resume_id: str):
    """
    Parse resume asynchronously.
    - Extracts text from PDF/DOCX
    - Extracts skills, experience, job titles
    - Sends to OpenAI for skill extraction
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        
        if resume.is_parsed:
            logger.info(f"Resume {resume_id} already parsed")
            return {
                'resume_id': resume_id,
                'status': 'already_parsed'
            }
        
        logger.info(f"Starting parse for resume: {resume_id}")
        
        # Download resume from Supabase
        storage_service = ResumeStorageService()
        file_content = storage_service.download_resume(resume.supabase_path)
        
        # Parse based on file type
        parser = ResumeParser()
        parsed_text = parser.parse_resume(file_content, resume.file_type)
        
        # Update resume with parsed text
        resume.parsed_text = parsed_text
        resume.is_parsed = True
        resume.parsed_at = timezone.now()
        resume.save()
        
        # Extract information from text
        skills = parser.extract_skills(parsed_text)
        experience = parser.extract_experience(parsed_text)
        job_titles = parser.extract_job_titles(parsed_text)
        contact_info = parser.extract_contact_info(parsed_text)
        
        # Update resume with extracted info
        resume.extracted_skills = skills
        resume.extracted_experience = experience
        resume.extracted_job_titles = job_titles
        resume.save()
        
        # Create version record
        ResumeVersion.objects.create(
            resume=resume,
            version_number=resume.version,
            parsed_text=parsed_text,
            extracted_skills=skills,
            extracted_experience=experience,
            extracted_job_titles=job_titles,
            change_reason='Initial upload and parsing'
        )
        
        # Trigger OpenAI skill extraction
        extract_skills_with_openai.delay(resume_id)
        
        # Clear cache
        cache.delete(f'resume_{resume.user.id}_data')
        cache.delete(f'resume_{resume.user.id}_stats')
        
        logger.info(f"Resume {resume_id} parsed successfully")
        
        return {
            'resume_id': resume_id,
            'status': 'parsed',
            'skills_count': len(skills),
            'experience_years': experience,
            'job_titles': job_titles
        }
        
    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found")
        return {'error': 'Resume not found'}
        
    except SoftTimeLimitExceeded:
        logger.error(f"Soft time limit exceeded for resume {resume_id}")
        self.retry(countdown=60)
        
    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, soft_time_limit=120)
def extract_skills_with_openai(self, resume_id: str):
    """
    Use OpenAI to extract skills from resume.
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        
        if not resume.parsed_text:
            logger.warning(f"Resume {resume_id} has no parsed text")
            return {'error': 'No parsed text available'}
        
        logger.info(f"Extracting skills with OpenAI for resume: {resume_id}")
        
        # Call FastAPI service for OpenAI extraction
        with httpx.Client() as client:
            response = client.post(
                os.getenv('FASTAPI_BASE_URL', 'http://localhost:8001').rstrip('/') + '/api/ai/extract-skills',

                json={'resume_text': resume.parsed_text[:4000]},
                timeout=30.0
            )
        
        if response.status_code != 200:
            error_msg = f"OpenAI extraction failed: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        data = response.json()
        
        # Update resume with extracted data
        resume.extracted_skills = data.get('skills', resume.extracted_skills)
        resume.extracted_experience = data.get('experience_years', resume.extracted_experience)
        resume.extracted_job_titles = data.get('job_titles', resume.extracted_job_titles)
        resume.is_processed = True
        resume.processed_at = timezone.now()
        resume.save()
        
        # Update user preferences
        user = resume.user
        if 'skills' not in user.preferences:
            user.preferences['skills'] = []
        user.preferences['skills'] = list(set(
            user.preferences.get('skills', []) + resume.extracted_skills
        ))
        user.save()
        
        logger.info(f"OpenAI extraction completed for resume: {resume_id}")
        
        return {
            'resume_id': resume_id,
            'status': 'processed',
            'skills': resume.extracted_skills,
            'experience_years': resume.extracted_experience,
            'job_titles': resume.extracted_job_titles
        }
        
    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found")
        return {'error': 'Resume not found'}
        
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def tailor_resume_async(self, resume_id: str, job_id: str):
    """
    Tailor resume for a specific job using OpenAI.
    """
    try:
        from jobs.models import JobListing
        
        resume = Resume.objects.get(id=resume_id)
        job = JobListing.objects.get(id=job_id)
        
        if not resume.parsed_text:
            logger.warning(f"Resume {resume_id} has no parsed text")
            return {'error': 'Resume has no parsed text'}
        
        logger.info(f"Tailoring resume {resume_id} for job {job_id}")
        
        # Call FastAPI service for tailoring using a regular client because this is a
        # synchronous Celery task, not an async coroutine context.
        with httpx.Client() as client:
            response = client.post(
                os.getenv('FASTAPI_BASE_URL', 'http://localhost:8001').rstrip('/') + '/api/resumes/tailor',
                json={
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                    'resume_url': resume.supabase_url,
                },
                timeout=120.0
            )
        
        if response.status_code != 200:
            error_msg = f"Tailoring failed: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        data = response.json()
        
        # Create tailored resume version
        with transaction.atomic():
            # Increment version for original resume
            resume.version += 1
            resume.save()
            
            # Create tailored resume record
            tailored = Resume.objects.create(
                user=resume.user,
                name=f"{resume.get_filename()} - Tailored for {job.company}",
                supabase_url=resume.supabase_url,
                supabase_path=resume.supabase_path,
                supabase_bucket=resume.supabase_bucket,
                file_size=resume.file_size,
                file_type=resume.file_type,
                parsed_text=data.get('tailored_text', ''),
                extracted_skills=data.get('keywords_added', []),
                extracted_experience=resume.extracted_experience,
                extracted_job_titles=resume.extracted_job_titles,
                is_default=False,
                is_tailored=True,
                tailored_for_job=job,
                tailored_from=resume,
                changes_summary=data.get('changes', {}),
                version=resume.version
            )
            
            # Create version record for tailored resume
            ResumeVersion.objects.create(
                resume=tailored,
                version_number=tailored.version,
                parsed_text=tailored.parsed_text,
                extracted_skills=tailored.extracted_skills,
                extracted_experience=tailored.extracted_experience,
                extracted_job_titles=tailored.extracted_job_titles,
                job=job,
                change_reason=f'Tailored for {job.title} at {job.company}',
                changes_summary=data.get('changes', {})
            )
            
            # Create version record for original resume
            ResumeVersion.objects.create(
                resume=resume,
                version_number=resume.version,
                parsed_text=resume.parsed_text,
                extracted_skills=resume.extracted_skills,
                extracted_experience=resume.extracted_experience,
                extracted_job_titles=resume.extracted_job_titles,
                change_reason=f'Version increment before tailoring for {job.title}'
            )
        
        # Clear cache
        cache.delete(f'resume_{resume.user.id}_data')
        cache.delete(f'resume_{resume.user.id}_stats')
        
        logger.info(f"Resume tailored successfully: {tailored.id}")
        
        return {
            'resume_id': str(tailored.id),
            'original_resume_id': str(resume.id),
            'job_id': str(job_id),
            'status': 'tailored',
            'message': 'Resume tailored successfully'
        }
        
    except (Resume.DoesNotExist, JobListing.DoesNotExist) as e:
        logger.error(f"Object not found: {str(e)}")
        return {'error': str(e)}
        
    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))




@shared_task
def cleanup_orphaned_resumes():
    """
    Clean up orphaned resume files in Supabase.
    """
    try:
        storage_service = ResumeStorageService()
        
        # Get all users
        from users.models import User
        users = User.objects.all()
        
        deleted_count = 0
        
        for user in users:
            # List files in user's folder
            folder_path = f"users/{str(user.id)}"
            files = storage_service.client.list_files(storage_service.BUCKET_NAME, folder_path)
            
            for file in files:
                file_path = f"{folder_path}/{file['name']}"
                # Check if resume exists in database
                exists = Resume.objects.filter(
                    supabase_path=file_path
                ).exists()
                
                if not exists:
                    # Delete orphaned file
                    storage_service.delete_resume(str(user.id), file_path)
                    deleted_count += 1
                    logger.info(f"Deleted orphaned file: {file_path}")
        
        return {
            'deleted_count': deleted_count,
            'status': 'cleanup_completed'
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return {'error': str(e)}

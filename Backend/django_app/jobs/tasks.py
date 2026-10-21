# backend/django_app/jobs/tasks.py (add this task)
import logging
from celery import shared_task
from django.db import transaction
from django.utils.timezone import now

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def store_apify_jobs(self, user_id: str, jobs: list):
    """
    Store Apify scraped jobs in the Django database.
    """
    try:
        from jobs.models import JobListing
        from users.models import User
        
        user = User.objects.get(id=user_id)
        created_count = 0
        skipped_count = 0
        errors = []
        
        for job_data in jobs:
            try:
                with transaction.atomic():
                    # Check if job already exists
                    job, created = JobListing.objects.get_or_create(
                        url=job_data.get('url', ''),
                        source='linkedin',
                        defaults={
                            'title': job_data.get('title', 'Unknown')[:255],
                            'company': job_data.get('company', 'Unknown')[:255],
                            'company_logo': job_data.get('company_logo', '')[:500],
                            'company_website': job_data.get('company_website', '')[:500],
                            'company_industry': job_data.get('company_industry', '')[:255],
                            'description': job_data.get('description', ''),
                            'location': job_data.get('location', '')[:255],
                            'external_id': job_data.get('external_id', '')[:255],
                            'posted_date': job_data.get('posted_date'),
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'salary_currency': job_data.get('salary_currency', 'USD')[:3],
                            'employment_type': job_data.get('employment_type', '')[:50],
                            'experience_level': job_data.get('experience_level', '')[:50],
                            'is_remote': job_data.get('is_remote', False),
                            'is_active': True,
                        }
                    )
                    
                if created:
                    created_count += 1
                else:
                    skipped_count += 1
            
            except Exception as e:
                logger.error(f"Failed to store job: {str(e)}")
                errors.append(str(e))
                continue
        
        # Trigger match score calculation for new jobs
        if created_count > 0:
            from .tasks import calculate_match_scores_for_user
            calculate_match_scores_for_user.delay(user_id)
        
        return {
            'created': created_count,
            'skipped': skipped_count,
            'total': len(jobs),
            'errors': errors[:5]  # Return first 5 errors
        }
        
    except Exception as e:
        logger.error(f"Failed to store Apify jobs: {str(e)}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))






# # backend/django_app/jobs/tasks.py
# from celery import shared_task
# from celery.utils.log import get_task_logger
# from django.core.cache import cache
# from .models import JobListing
# from resumes.models import Resume
# import requests
# import json
# import logging

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3)
# def discover_jobs_for_user(self, user_id, preferences):
#     """Discover jobs for a user based on preferences"""
#     try:
#         from users.models import User
#         user = User.objects.get(id=user_id)
        
#         # Call FastAPI job discovery service
#         response = requests.post(
#             'http://fastapi:8001/api/jobs/discover',
#             json={
#                 'user_id': user_id,
#                 'preferences': preferences or user.preferences
#             },
#             timeout=120
#         )
        
#         if response.status_code == 200:
#             data = response.json()
            
#             # Store discovered jobs
#             jobs_created = 0
#             for job_data in data.get('jobs', []):
#                 job, created = JobListing.objects.get_or_create(
#                     url=job_data.get('url'),
#                     source=job_data.get('source', 'linkedin'),
#                     defaults={
#                         'title': job_data.get('title', 'Unknown'),
#                         'company': job_data.get('company', 'Unknown'),
#                         'description': job_data.get('description', ''),
#                         'location': job_data.get('location', 'Remote'),
#                         'posted_date': job_data.get('posted_date'),
#                         'is_active': True
#                     }
#                 )
#                 if created:
#                     jobs_created += 1
            
#             # Trigger match calculation for new jobs
#             if jobs_created > 0:
#                 new_jobs = JobListing.objects.filter(
#                     match_score__isnull=True,
#                     is_active=True
#                 ).values_list('id', flat=True)[:50]
                
#                 if new_jobs:
#                     calculate_match_scores.delay(
#                         user_id,
#                         list(new_jobs),
#                         str(user.get_default_resume().id) if user.get_default_resume() else None
#                     )
            
#             return {
#                 'user_id': user_id,
#                 'jobs_found': len(data.get('jobs', [])),
#                 'jobs_created': jobs_created,
#                 'task_id': self.request.id
#             }
#         else:
#             logger.error(f"Job discovery failed: {response.text}")
#             return {'error': 'Job discovery failed'}
            
#     except Exception as e:
#         logger.error(f"Error discovering jobs: {str(e)}")
#         self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


# @shared_task(bind=True, max_retries=3)
# def calculate_match_scores(self, user_id, job_ids, resume_id=None):
#     """Calculate match scores for multiple jobs"""
#     try:
#         from users.models import User
#         user = User.objects.get(id=user_id)
        
#         if not resume_id:
#             resume = user.get_default_resume()
#             if not resume:
#                 return {'error': 'No resume found'}
#             resume_id = str(resume.id)
        
#         resume = Resume.objects.get(id=resume_id)
        
#         # Call FastAPI match service
#         response = requests.post(
#             'http://fastapi:8001/api/ai/batch-match',
#             json={
#                 'user_id': user_id,
#                 'resume_id': resume_id,
#                 'resume_text': resume.parsed_text,
#                 'job_ids': job_ids
#             },
#             timeout=180
#         )
        
#         if response.status_code == 200:
#             data = response.json()
            
#             # Update jobs with match scores
#             for result in data.get('results', []):
#                 JobListing.objects.filter(id=result.get('job_id')).update(
#                     match_score=result.get('match_score'),
#                     missing_skills=result.get('missing_skills', []),
#                     fit_analysis=result.get('fit_analysis', ''),
#                     recommended_keywords=result.get('recommended_keywords', [])
#                 )
            
#             return {
#                 'user_id': user_id,
#                 'jobs_processed': len(data.get('results', [])),
#                 'task_id': self.request.id
#             }
#         else:
#             logger.error(f"Match calculation failed: {response.text}")
#             return {'error': 'Match calculation failed'}
            
#     except Exception as e:
#         logger.error(f"Error calculating matches: {str(e)}")
#         self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


# def calculate_match_score_for_job(user_id, job_id, resume_id):
#     """Calculate match score for a single job"""
#     results = calculate_match_scores(user_id, [job_id], resume_id)
#     return results
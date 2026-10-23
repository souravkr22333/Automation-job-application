# backend/django_app/jobs/tasks.py
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
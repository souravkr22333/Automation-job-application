# backend/django_app/applications/tasks.py
import uuid
import hashlib
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction, models
from django.core.cache import cache
from django.utils.timezone import now
from .models import ApplicationQueue, Application, CoverLetter
from jobs.models import JobListing
from resumes.models import Resume
import requests
import json
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_queue_item(self, queue_item_id):
    """Process a single queue item"""
    try:
        queue_item = ApplicationQueue.objects.get(id=queue_item_id)
        
        if queue_item.status == 'done':
            return {'status': 'already_processed', 'id': str(queue_item.id)}
        
        # Update status
        queue_item.status = ApplicationQueue.Status.PROCESSING
        queue_item.attempts += 1
        queue_item.last_attempt_at = now()
        queue_item.save()
        
        # Get user and job
        user = queue_item.user
        job = queue_item.job
        
        # Step 1: Tailor resume
        tailor_response = requests.post(
            'http://fastapi:8001/api/resumes/tailor',
            json={
                'user_id': str(user.id),
                'job_id': str(job.id),
                'resume_id': str(queue_item.tailored_resume.id) if queue_item.tailored_resume else None
            },
            timeout=60
        )
        
        if tailor_response.status_code != 200:
            raise Exception(f"Resume tailoring failed: {tailor_response.text}")
        
        tailor_data = tailor_response.json()
        tailored_resume_id = tailor_data.get('resume_id')
        
        # Get tailored resume
        tailored_resume = Resume.objects.get(id=tailored_resume_id)
        queue_item.tailored_resume = tailored_resume
        queue_item.save()
        
        # Step 2: Generate cover letter
        cover_response = requests.post(
            'http://fastapi:8001/api/ai/generate-cover-letter',
            json={
                'user_id': str(user.id),
                'job_id': str(job.id),
                'resume_id': str(tailored_resume.id),
                'tone': 'professional'
            },
            timeout=60
        )
        
        if cover_response.status_code != 200:
            raise Exception(f"Cover letter generation failed: {cover_response.text}")
        
        cover_data = cover_response.json()
        cover_letter_text = cover_data.get('cover_letter', '')
        
        # Store cover letter
        cover_letter = CoverLetter.objects.create(
            user=user,
            job=job,
            content=cover_letter_text,
            tone='professional'
        )
        
        queue_item.cover_letter = cover_letter_text
        queue_item.cover_letter_id = cover_letter.id
        queue_item.save()
        
        # Step 3: Submit application
        submit_response = requests.post(
            'http://fastapi:8001/api/applications/submit',
            json={
                'queue_item_id': str(queue_item.id),
                'user_id': str(user.id),
                'job_id': str(job.id),
                'tailored_resume_id': str(tailored_resume.id),
                'cover_letter': cover_letter_text
            },
            timeout=120
        )
        
        if submit_response.status_code != 200:
            raise Exception(f"Application submission failed: {submit_response.text}")
        
        submit_data = submit_response.json()
        
        # Create application record
        with transaction.atomic():
            application = Application.objects.create(
                user=user,
                job=job,
                resume=tailored_resume,
                cover_letter=cover_letter_text,
                status=Application.Status.APPLIED,
                application_url=submit_data.get('application_url', ''),
                applied_at=now()
            )
            
            # Update queue item
            queue_item.status = ApplicationQueue.Status.DONE
            queue_item.submitted_at = now()
            queue_item.application_url = submit_data.get('application_url', '')
            queue_item.save()
        
        # Clear cache
        cache.delete(f'queue_{user.id}')
        cache.delete(f'applications_{user.id}')
        
        return {
            'status': 'success',
            'queue_item_id': str(queue_item.id),
            'application_id': str(application.id),
            'message': 'Application submitted successfully'
        }
        
    except ApplicationQueue.DoesNotExist:
        logger.error(f"Queue item {queue_item_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing queue item {queue_item_id}: {str(e)}")
        
        # Update queue item status
        try:
            queue_item = ApplicationQueue.objects.get(id=queue_item_id)
            if queue_item.attempts >= queue_item.max_attempts:
                queue_item.status = ApplicationQueue.Status.FAILED
                queue_item.error_message = str(e)
                queue_item.save()
            else:
                queue_item.status = ApplicationQueue.Status.RETRYING
                queue_item.error_message = str(e)
                queue_item.save()
                self.retry(exc=e, countdown=60 * (2 ** queue_item.attempts))
        except:
            pass
        
        raise


@shared_task
def process_queue_batch(user_id=None):
    """Process a batch of queue items"""
    try:
        # Get queued items
        query = ApplicationQueue.objects.filter(
            status__in=[ApplicationQueue.Status.QUEUED, ApplicationQueue.Status.RETRYING],
            attempts__lt=models.F('max_attempts')
        )
        
        if user_id:
            query = query.filter(user_id=user_id)
        
        queue_items = query.order_by('position', 'created_at')[:10]
        
        results = []
        for item in queue_items:
            result = process_queue_item.delay(str(item.id))
            results.append({
                'queue_item_id': str(item.id),
                'task_id': result.id,
                'job': item.job.title
            })
        
        return {
            'processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error processing queue batch: {str(e)}")
        return {'error': str(e)}


@shared_task
def generate_cover_letter_async(user_id, job_id, resume_id=None, tone='professional', additional_points=''):
    """Generate a cover letter asynchronously"""
    try:
        from users.models import User
        user = User.objects.get(id=user_id)
        job = JobListing.objects.get(id=job_id)
        
        if not resume_id:
            resume = user.get_default_resume()
            if not resume:
                return {'error': 'No resume found'}
            resume_id = str(resume.id)
        
        resume = Resume.objects.get(id=resume_id)
        
        # Call FastAPI
        response = requests.post(
            'http://fastapi:8001/api/ai/generate-cover-letter',
            json={
                'user_id': user_id,
                'job_id': job_id,
                'resume_text': resume.parsed_text,
                'job_description': job.description,
                'job_title': job.title,
                'company': job.company,
                'tone': tone,
                'additional_points': additional_points
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Store cover letter
            cover_letter = CoverLetter.objects.create(
                user=user,
                job=job,
                content=data.get('cover_letter', ''),
                tone=tone
            )
            
            return {
                'cover_letter_id': str(cover_letter.id),
                'cover_letter': cover_letter.content,
                'message': 'Cover letter generated successfully'
            }
        else:
            logger.error(f"Cover letter generation failed: {response.text}")
            return {'error': 'Cover letter generation failed'}
            
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise


@shared_task
def cleanup_failed_applications():
    """Clean up failed applications older than 7 days"""
    from datetime import timedelta
    from django.utils.timezone import now
    
    cutoff = now() - timedelta(days=7)
    failed = ApplicationQueue.objects.filter(
        status=ApplicationQueue.Status.FAILED,
        updated_at__lt=cutoff
    )
    
    count = failed.count()
    failed.delete()
    
    return {'cleaned': count}


@shared_task
def process_queue_retry():
    """Retry failed queue items"""
    from datetime import timedelta
    from django.utils.timezone import now
    
    retry_after = now() - timedelta(hours=1)
    
    failed = ApplicationQueue.objects.filter(
        status=ApplicationQueue.Status.FAILED,
        updated_at__lt=retry_after,
        attempts__lt=models.F('max_attempts')
    )
    
    for item in failed:
        item.status = ApplicationQueue.Status.QUEUED
        item.save()
        process_queue_item.delay(str(item.id))
    
    return {'retried': failed.count()}
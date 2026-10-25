# backend/django_app/applications/tasks.py
from celery import shared_task
from django.db import transaction, models
from django.core.cache import cache
from django.utils.timezone import now
from .models import ApplicationQueue, Application, CoverLetter
from jobs.models import JobListing
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_queue_item(self, queue_item_id):
    """Process a single queue item"""
    try:
        queue_item = ApplicationQueue.objects.get(id=queue_item_id)
        if queue_item.status in (
            ApplicationQueue.Status.DONE,
            ApplicationQueue.Status.PENDING_CONFIRMATION,
            ApplicationQueue.Status.PROCESSING,
            ApplicationQueue.Status.GENERATING_RESUME,
            ApplicationQueue.Status.APPLYING,
        ):
            return {'status': 'already_processed', 'queue_item_id': str(queue_item.id)}

        user = queue_item.user
        job = queue_item.job
        existing_application = Application.objects.filter(user=user, job=job).first()
        if existing_application:
            queue_item.status = ApplicationQueue.Status.DONE
            queue_item.application_url = existing_application.application_url
            queue_item.save(update_fields=['status', 'application_url', 'updated_at'])
            return {
                'status': 'already_applied',
                'queue_item_id': str(queue_item.id),
                'application_id': str(existing_application.id),
            }

        today_count = Application.objects.filter(
            user=user,
            applied_at__date=now().date(),
        ).count() + ApplicationQueue.objects.filter(
            user=user,
            status=ApplicationQueue.Status.PENDING_CONFIRMATION,
            updated_at__date=now().date(),
        ).count()
        if today_count >= 10:
            queue_item.status = ApplicationQueue.Status.LIMIT_REACHED
            queue_item.error_message = 'Daily auto-apply limit reached (10 applications).'
            queue_item.save(update_fields=['status', 'error_message', 'updated_at'])
            return {'status': 'limit_reached', 'queue_item_id': str(queue_item.id)}

        queue_item.status = ApplicationQueue.Status.GENERATING_RESUME
        queue_item.attempts += 1
        queue_item.last_attempt_at = now()
        queue_item.save()
        from applications.views import ApplicationQueueViewSet, _create_tailored_resume_pdf

        resume = (
            queue_item.tailored_resume.original_resume
            if queue_item.tailored_resume and queue_item.tailored_resume.original_resume
            else user.get_default_resume()
        )
        if not resume:
            raise RuntimeError('No resume found. Please upload a resume first.')

        service = ApplicationQueueViewSet()
        tailoring_result = service._tailor_resume(resume, job)
        tailored_pdf = _create_tailored_resume_pdf(
            user=user,
            job=job,
            original_resume=resume,
            tailored_text=tailoring_result['tailored_resume'].parsed_text,
            changes=tailoring_result.get('changes', {}),
            keywords_added=[],
        )
        if not tailored_pdf.supabase_url:
            raise RuntimeError('Tailored resume PDF could not be stored')

        cover_letter_result = service._generate_cover_letter(resume, job, 'professional')
        cover_letter = cover_letter_result['cover_letter_obj']
        queue_item.tailored_resume = tailored_pdf
        queue_item.cover_letter = cover_letter_result['cover_letter']
        queue_item.cover_letter_id = cover_letter.id
        queue_item.status = ApplicationQueue.Status.APPLYING
        queue_item.save()

        submit_data = service._submit_application(
            user,
            job,
            queue_item,
            tailored_pdf,
            cover_letter_result['cover_letter'],
        )
        if submit_data['status'] == 'pending_confirmation':
            queue_item.status = ApplicationQueue.Status.PENDING_CONFIRMATION
            queue_item.application_url = submit_data.get('application_url') or ''
            queue_item.error_message = submit_data.get('message', '')
            queue_item.save()
            return {
                'status': 'pending_confirmation',
                'queue_item_id': str(queue_item.id),
                'message': queue_item.error_message,
            }

        with transaction.atomic():
            application = Application.objects.create(
                user=user,
                job=job,
                resume=tailoring_result['tailored_resume'],
                cover_letter=cover_letter_result['cover_letter'],
                status=Application.Status.APPLIED,
                application_url=submit_data.get('application_url') or job.url,
                applied_at=now()
            )
            job.is_applied = True
            job.save(update_fields=['is_applied'])
            cover_letter.is_used = True
            cover_letter.save(update_fields=['is_used'])

            queue_item.status = ApplicationQueue.Status.DONE
            queue_item.submitted_at = now()
            queue_item.application_url = submit_data.get('application_url') or job.url
            queue_item.error_message = ''
            queue_item.save()

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
        
        try:
            queue_item = ApplicationQueue.objects.get(id=queue_item_id)
        except ApplicationQueue.DoesNotExist:
            logger.exception("Queue item %s disappeared while recording task failure", queue_item_id)
            raise e

        if isinstance(e, ApplicationSubmissionError):
            queue_item.status = ApplicationQueue.Status.FAILED
            queue_item.error_message = str(e)[:500]
            queue_item.save(update_fields=['status', 'error_message', 'updated_at'])
            raise

        from applications.views import ApplicationSubmissionError
        if (
            queue_item.status == ApplicationQueue.Status.APPLYING
            and not isinstance(e, ApplicationSubmissionError)
        ):
            queue_item.status = ApplicationQueue.Status.PENDING_CONFIRMATION
            queue_item.error_message = (
                'Submission outcome is uncertain. Verify the application on the job site before retrying.'
            )
            queue_item.save(update_fields=['status', 'error_message', 'updated_at'])
            return {
                'status': 'pending_confirmation',
                'queue_item_id': str(queue_item.id),
                'message': queue_item.error_message,
            }

        queue_item.error_message = str(e)[:500]
        if queue_item.attempts >= queue_item.max_attempts:
            queue_item.status = ApplicationQueue.Status.FAILED
            queue_item.save(update_fields=['status', 'error_message', 'updated_at'])
        else:
            queue_item.status = ApplicationQueue.Status.RETRYING
            queue_item.save(update_fields=['status', 'error_message', 'updated_at'])
            raise self.retry(exc=e, countdown=60 * (2 ** queue_item.attempts))

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
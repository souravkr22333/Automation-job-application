# backend/django_app/applications/views.py

import httpx
import logging
import uuid
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from .models import Application, ApplicationQueue, CoverLetter
from jobs.models import JobListing
from resumes.models import Resume, TailoredResume
from resumes.services import ResumeStorageService, PDFGenerator
from .serializers import ApplicationSerializer, CoverLetterSerializer

logger = logging.getLogger(__name__)


class ApplicationSubmissionError(RuntimeError):
    """A submission was explicitly rejected before a completed application was confirmed."""


def _create_tailored_resume_pdf(user, job, original_resume, tailored_text, changes, keywords_added):
    """
    Generate a NEW PDF from the AI-tailored resume text,
    upload to Supabase 'Tailored resume' bucket,
    and return a TailoredResume instance.
    Always creates the TailoredResume DB record — even if Supabase upload fails,
    so the tailored resume is never lost.
    """
    storage = ResumeStorageService()

    # Use user's name for filename: "CandidateName_JobTitle.pdf"
    user_name = user.name or user.email.split('@')[0] if user.email else 'Candidate'
    safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in user_name)[:30]
    safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in job.title)[:30]
    filename = f"{safe_name}_{safe_title}.pdf"

    # Default values in case PDF generation or upload fails
    supabase_url = ''
    supabase_path = ''
    supabase_bucket = TailoredResume.TAILORED_BUCKET
    file_size = 0
    file_type = 'application/pdf'

    try:
        pdf_bytes = PDFGenerator.generate_resume_pdf(
            resume_text=tailored_text,
            title=""  # Empty title - no heading at top of PDF
        )

        upload_result = storage.upload_bytes(
            bucket_name=TailoredResume.TAILORED_BUCKET,
            user_id=str(user.id),
            file_bytes=pdf_bytes,
            filename=filename,
            content_type='application/pdf'
        )

        supabase_url = upload_result['public_url']
        supabase_path = upload_result['path']
        supabase_bucket = upload_result['bucket']
        file_size = upload_result['file_size']
        file_type = upload_result['content_type']

    except Exception as pdf_err:
        logger.warning(f"PDF generation/upload failed (saving TailoredResume without PDF): {str(pdf_err)}")

    tailored_resume = TailoredResume.objects.create(
        user=user,
        job=job,
        original_resume=original_resume,
        name=filename,
        supabase_url=supabase_url,
        supabase_path=supabase_path,
        supabase_bucket=supabase_bucket,
        file_size=file_size,
        file_type=file_type,
        tailored_text=tailored_text,
        changes_summary=changes,
        keywords_added=keywords_added,
    )

    return tailored_resume


class ApplicationQueueViewSet(viewsets.ModelViewSet):
    """Application queue management with auto-generate and apply endpoints"""
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Use ApplicationQueueSerializer for queue-related actions"""
        if hasattr(self, 'action') and self.action in ('list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'status', 'auto_generate', 'auto_apply', 'bulk_apply'):
            from .serializers import ApplicationQueueSerializer
            return ApplicationQueueSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        # Return ApplicationQueue items for this user
        return ApplicationQueue.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """Single entry point for applying to a job."""
        job_id = request.data.get('job_id')
        resume_id = request.data.get('resume_id')
        tone = request.data.get('tone', 'professional')

        if not job_id:
            return Response({
                'error': 'job_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = JobListing.objects.get(id=job_id)
            logger.info(f"Applying to: {job.title} at {job.company}")

            if resume_id:
                resume = Resume.objects.get(id=resume_id, user=request.user)
            else:
                resume = request.user.get_default_resume()
                if not resume:
                    return Response({
                        'error': 'No resume found. Please upload a resume first.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Using resume: {resume.name}")

            logger.info("Tailoring resume...")
            tailoring_result = self._tailor_resume(resume, job)

            logger.info("Generating cover letter...")
            cover_letter_result = self._generate_cover_letter(resume, job, tone)

            logger.info("Submitting application...")
            submission_result = self._submit_application(
                request.user, job,
                tailoring_result['tailored_resume'],
                cover_letter_result['cover_letter']
            )

            logger.info("Saving application record...")
            application = Application.objects.create(
                user=request.user,
                job=job,
                resume=tailoring_result['tailored_resume'],
                cover_letter=cover_letter_result['cover_letter'],
                status=Application.Status.APPLIED,
                application_url=job.url,
                applied_at=now()
            )

            job.is_applied = True
            job.save()

            cover_letter_result['cover_letter_obj'].is_used = True
            cover_letter_result['cover_letter_obj'].save()

            return Response({
                'status': 'success',
                'job_title': job.title,
                'company': job.company,
                'application_id': str(application.id),
                'application_status': application.status,
                'application_url': application.application_url,
                'message': 'Application submitted successfully!',
                'tailored_resume_id': str(tailoring_result['tailored_resume'].id),
                'cover_letter_id': str(cover_letter_result['cover_letter_obj'].id),
                'match_score': job.match_score
            }, status=status.HTTP_201_CREATED)

        except JobListing.DoesNotExist:
            return Response({
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Resume.DoesNotExist:
            return Response({
                'error': 'Resume not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({
                'error': f'Application failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _tailor_resume(self, resume, job):
        """Tailor resume for specific job"""
        try:
            response = httpx.post(
                f'{settings.FASTAPI_BASE_URL}/api/resumes/tailor',
                json={
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                    'resume_url': resume.supabase_url,
                },
                timeout=180.0
            )

            if response.status_code != 200:
                raise Exception(f"Tailoring failed: {response.text}")

            data = response.json()

            tailored_resume = Resume.objects.create(
                user=resume.user,
                name=f"{resume.name} - Tailored for {job.company}",
                supabase_url=resume.supabase_url,
                supabase_path=resume.supabase_path,
                supabase_bucket=resume.supabase_bucket,
                file_size=resume.file_size,
                file_type=resume.file_type,
                parsed_text=data.get('tailored_text', resume.parsed_text),
                is_tailored=True,
                tailored_for_job=job,
                tailored_from=resume,
                changes_summary=data.get('changes', {}),
                version=resume.version + 1
            )

            return {
                'tailored_resume': tailored_resume,
                'changes': data.get('changes', {})
            }

        except Exception as e:
            logger.error(f"Tailoring error: {str(e)}")
            import traceback
            logger.error(f"Tailoring traceback: {traceback.format_exc()}")
            raise

    def _generate_cover_letter(self, resume, job, tone='professional'):
        """Generate cover letter for job"""
        try:
            response = httpx.post(
                f'{settings.FASTAPI_BASE_URL}/api/ai/generate-cover-letter',
                json={
                    'user_id': str(resume.user.id),
                    'job_id': str(job.id),
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                    'tone': tone,
                    'additional_points': ''
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Cover letter generation failed: {response.text}")

            data = response.json()
            cover_letter_text = data.get('cover_letter', '')

            cover_letter = CoverLetter.objects.create(
                user=resume.user,
                job=job,
                content=cover_letter_text,
                tone=tone
            )

            return {
                'cover_letter': cover_letter_text,
                'cover_letter_obj': cover_letter
            }

        except Exception as e:
            logger.error(f"Cover letter error: {str(e)}")
            raise

    def _submit_application(self, user, job, queue_item, tailored_resume, cover_letter):
        """Submit application via FastAPI/Playwright"""
        if not settings.FASTAPI_INTERNAL_TOKEN:
            raise RuntimeError('AUTO_APPLY_INTERNAL_TOKEN is not configured')

        if not tailored_resume.supabase_url:
            raise RuntimeError('Tailored resume PDF is not available for submission')

        try:
            response = httpx.post(
                f'{settings.FASTAPI_BASE_URL}/api/applications/submit',
                json={
                    'queue_item_id': str(queue_item.id),
                    'user_data': {
                        'name': user.name,
                        'email': user.email,
                        'phone': user.phone,
                    },
                    'job': {
                        'id': str(job.id),
                        'url': job.url,
                        'title': job.title,
                        'company': job.company,
                    },
                    'resume_url': tailored_resume.supabase_url,
                    'cover_letter': cover_letter,
                    'platform': job.source or 'unknown',
                },
                headers={'X-Internal-Token': settings.FASTAPI_INTERNAL_TOKEN},
                timeout=300.0
            )

            if 400 <= response.status_code < 500:
                raise ApplicationSubmissionError(f"Submission failed: {response.text}")
            if response.status_code != 200:
                raise RuntimeError(f"Submission service error: {response.text}")

            result = response.json()
            if result.get('status') not in ('success', 'pending_confirmation'):
                raise RuntimeError(
                    result.get('message') or 'Submission service returned an invalid status'
                )
            return result

        except Exception as e:
            logger.error(f"Submission error: {str(e)}")
            raise

    def _get_user_auto_apply_count(self, user):
        """Count confirmed and unconfirmed submissions against the daily limit."""
        applied_count = Application.objects.filter(
            user=user,
            applied_at__date=now().date()
        ).count()
        pending_count = ApplicationQueue.objects.filter(
            user=user,
            status=ApplicationQueue.Status.PENDING_CONFIRMATION,
            updated_at__date=now().date(),
        ).count()
        return applied_count + pending_count

    @action(detail=False, methods=['post'])
    def auto_apply(self, request):
        """Auto-generate a tailored resume and apply to each queued job, capped at 10 jobs/day."""
        job_ids = request.data.get('job_ids', [])
        resume_id = request.data.get('resume_id')
        limit = 10

        if not isinstance(job_ids, list) or not job_ids:
            return Response({
                'error': 'job_ids is required (array of job IDs)'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            job_ids = list(dict.fromkeys(str(uuid.UUID(str(job_id))) for job_id in job_ids))
        except (TypeError, ValueError, AttributeError):
            return Response({
                'error': 'job_ids must contain valid job IDs'
            }, status=status.HTTP_400_BAD_REQUEST)

        used_today = self._get_user_auto_apply_count(request.user)
        remaining = limit - used_today
        already_applied_ids = {
            str(job_id) for job_id in
            Application.objects.filter(user=request.user, job_id__in=job_ids)
            .values_list('job_id', flat=True)
        }
        requested_new_count = sum(str(job_id) not in already_applied_ids for job_id in job_ids)
        if remaining <= 0 or requested_new_count > remaining:
            return Response({
                'detail': f'Auto-apply limit reached. You have used {used_today}/{limit} auto-applies today.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if resume_id:
            try:
                resume = Resume.objects.get(id=uuid.UUID(str(resume_id)), user=request.user)
            except (TypeError, ValueError, AttributeError):
                return Response({
                    'error': 'resume_id must be a valid resume ID'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Resume.DoesNotExist:
                return Response({
                    'error': 'Resume not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            resume = request.user.get_default_resume()
            if not resume:
                return Response({
                    'error': 'No resume found. Please upload a resume first.'
                }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for job_id in job_ids:
            queue_item = None
            try:
                job = JobListing.objects.get(id=job_id)
                existing_application = Application.objects.filter(
                    user=request.user,
                    job=job,
                ).first()
                if existing_application:
                    ApplicationQueue.objects.filter(
                        user=request.user,
                        job=job,
                    ).update(status=ApplicationQueue.Status.DONE)
                    results.append({
                        'job_id': str(job.id),
                        'status': 'already_applied',
                        'application_id': str(existing_application.id),
                        'message': 'An application for this job already exists',
                    })
                    continue

                existing_queue_item = ApplicationQueue.objects.filter(
                    user=request.user,
                    job=job,
                ).first()
                if (
                    existing_queue_item
                    and existing_queue_item.status == ApplicationQueue.Status.PENDING_CONFIRMATION
                ):
                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(existing_queue_item.id),
                        'status': 'pending_confirmation',
                        'message': existing_queue_item.error_message,
                    })
                    continue
                if (
                    existing_queue_item
                    and existing_queue_item.status in (
                        ApplicationQueue.Status.PROCESSING,
                        ApplicationQueue.Status.GENERATING_RESUME,
                        ApplicationQueue.Status.APPLYING,
                        ApplicationQueue.Status.RETRYING,
                    )
                ):
                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(existing_queue_item.id),
                        'status': 'processing',
                        'message': 'This application is already being processed',
                    })
                    continue

                queue_item, _ = ApplicationQueue.objects.get_or_create(
                    user=request.user,
                    job=job,
                    defaults={
                        'priority': ApplicationQueue.Priority.MEDIUM,
                        'position': ApplicationQueue.objects.filter(user=request.user).count() + 1,
                        'status': ApplicationQueue.Status.QUEUED,
                        'idempotency_key': f"{request.user.id}_{job_id}_{uuid.uuid4().hex[:8]}_auto_apply",
                        'source': job.source or 'linkedin',
                    }
                )

                queue_item.status = ApplicationQueue.Status.GENERATING_RESUME
                queue_item.error_message = ''
                queue_item.save()

                tailoring_result = self._tailor_resume(resume, job)
                tailored_pdf = _create_tailored_resume_pdf(
                    user=request.user,
                    job=job,
                    original_resume=resume,
                    tailored_text=tailoring_result['tailored_resume'].parsed_text,
                    changes=tailoring_result.get('changes', {}),
                    keywords_added=[],
                )
                if not tailored_pdf.supabase_url:
                    raise RuntimeError('Tailored resume PDF could not be stored')

                cover_letter_result = self._generate_cover_letter(resume, job, 'professional')

                queue_item.tailored_resume = tailored_pdf
                queue_item.cover_letter = cover_letter_result['cover_letter']
                queue_item.status = ApplicationQueue.Status.APPLYING
                queue_item.save()

                submission_result = self._submit_application(
                    request.user, job, queue_item, tailored_pdf,
                    cover_letter_result['cover_letter']
                )
                if submission_result['status'] == 'pending_confirmation':
                    queue_item.status = ApplicationQueue.Status.PENDING_CONFIRMATION
                    queue_item.application_url = submission_result.get('application_url') or ''
                    queue_item.error_message = submission_result.get('message', '')
                    queue_item.save()
                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(queue_item.id),
                        'status': 'pending_confirmation',
                        'message': queue_item.error_message,
                    })
                    continue

                application = Application.objects.create(
                    user=request.user,
                    job=job,
                    resume=tailoring_result['tailored_resume'],
                    cover_letter=cover_letter_result['cover_letter'],
                    status=Application.Status.APPLIED,
                    application_url=submission_result.get('application_url') or job.url,
                    applied_at=now()
                )

                job.is_applied = True
                job.save()
                cover_letter_result['cover_letter_obj'].is_used = True
                cover_letter_result['cover_letter_obj'].save(update_fields=['is_used'])

                queue_item.status = ApplicationQueue.Status.DONE
                queue_item.submitted_at = now()
                queue_item.application_url = submission_result.get('application_url') or job.url
                queue_item.error_message = ''
                queue_item.save()

                results.append({
                    'job_id': str(job.id),
                    'queue_item_id': str(queue_item.id),
                    'status': 'applied',
                    'application_id': str(application.id),
                    'message': 'Auto apply completed successfully'
                })
            except Exception as exc:
                try:
                    if queue_item:
                        uncertain_submission = (
                            queue_item.status == ApplicationQueue.Status.APPLYING
                            and not isinstance(exc, ApplicationSubmissionError)
                        )
                        queue_item.status = (
                            ApplicationQueue.Status.PENDING_CONFIRMATION
                            if uncertain_submission
                            else ApplicationQueue.Status.FAILED
                        )
                        queue_item.error_message = str(exc)[:500]
                        queue_item.save()
                    else:
                        uncertain_submission = False
                except Exception:
                    logger.exception("Failed to update queue status for job %s", job_id)
                logger.exception("Auto-apply failed for job %s", job_id)
                results.append({
                    'job_id': str(job_id),
                    'status': 'pending_confirmation' if uncertain_submission else 'failed',
                    'message': (
                        'Submission outcome is uncertain. Verify the application on the job site before retrying.'
                        if uncertain_submission
                        else str(exc)
                    )
                })

        return Response({
            'total': len(job_ids),
            'limit': limit,
            'used_today': self._get_user_auto_apply_count(request.user),
            'results': results,
        })

    @action(detail=False, methods=['post'])
    def auto_generate(self, request):
        """
        Auto-generate tailored resumes for jobs in the queue.
        For each job: tailors the default resume using AI, creates a new tailored Resume record,
        generates a PDF with the tailored content, uploads to Supabase, and creates a TailoredResume.
        """
        job_ids = request.data.get('job_ids', [])
        resume_id = request.data.get('resume_id')

        if not job_ids:
            return Response({
                'error': 'job_ids is required (array of job IDs)'
            }, status=status.HTTP_400_BAD_REQUEST)

        if resume_id:
            try:
                resume = Resume.objects.get(id=resume_id, user=request.user)
            except Resume.DoesNotExist:
                return Response({
                    'error': 'Resume not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            resume = request.user.get_default_resume()
            if not resume:
                return Response({
                    'error': 'No resume found. Please upload a resume first.'
                }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for job_id in job_ids:
            try:
                job = JobListing.objects.get(id=job_id)

                import hashlib
                import uuid
                idem_key_str = f"{request.user.id}_{job_id}_{uuid.uuid4().hex[:8]}_auto_generate"
                idempotency_key = hashlib.sha256(idem_key_str.encode()).hexdigest()

                queue_item, created = ApplicationQueue.objects.get_or_create(
                    user=request.user,
                    job=job,
                    defaults={
                        'priority': ApplicationQueue.Priority.MEDIUM,
                        'position': ApplicationQueue.objects.filter(user=request.user).count() + 1,
                        'status': ApplicationQueue.Status.QUEUED,
                        'idempotency_key': idempotency_key,
                        'source': job.source or 'linkedin',
                        'tailored_resume': None,
                        'tailored_resume_file': None,
                    }
                )

                if not created and queue_item.status not in [
                    ApplicationQueue.Status.QUEUED,
                    ApplicationQueue.Status.RETRYING
                ]:
                    queue_item.status = ApplicationQueue.Status.QUEUED
                    queue_item.error_message = ''
                    queue_item.attempts = 0
                    # Clear old references when re-queuing
                    queue_item.tailored_resume = None
                    queue_item.tailored_resume_file = None
                    queue_item.cover_letter = ''
                    queue_item.save()

                if queue_item.tailored_resume and queue_item.cover_letter:
                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(queue_item.id),
                        'title': job.title,
                        'company': job.company,
                        'status': 'already_generated',
                        'tailored': True,
                        'message': 'Resume already tailored for this job'
                    })
                    continue

                try:
                    logger.info(f"Tailoring resume for: {job.title} at {job.company}")
                    tailor_response = httpx.post(
                        'https://delightful-education-production-cd5d.up.railway.app/api/resumes/tailor',
                        #'http://localhost:8001/api/resumes/tailor',
                        json={
                            'resume_text': resume.parsed_text,
                            'job_description': job.description or '',
                            'job_title': job.title,
                            'company': job.company,
                            'resume_url': resume.supabase_url,
                            'user_id': str(request.user.id),
                            'job_id': str(job.id),
                            'resume_id': str(resume.id),
                        },
                        timeout=120.0
                    )

                    if tailor_response.status_code == 200:
                        tailor_data = tailor_response.json()
                        tailored_text = tailor_data.get('tailored_text', resume.parsed_text)
                        changes = tailor_data.get('changes', {})
                        keywords_added = tailor_data.get('keywords_added', [])

                        # Create tailored Resume record
                        tailored_name = f"{resume.name} - Tailored for {job.company}"
                        if len(tailored_name) > 255:
                            tailored_name = tailored_name[:252] + "..."

                        tailored_resume = Resume.objects.create(
                            user=resume.user,
                            name=tailored_name,
                            supabase_url=resume.supabase_url,
                            supabase_path=resume.supabase_path,
                            supabase_bucket=resume.supabase_bucket,
                            file_size=resume.file_size,
                            file_type=resume.file_type,
                            parsed_text=tailored_text,
                            is_default=False,
                            is_tailored=True,
                            tailored_for_job=job,
                            tailored_from=resume,
                            changes_summary=changes,
                            version=resume.version + 1,
                        )

                        # Generate PDF and create TailoredResume (stored in 'Tailored resume' bucket)
                        tailored_resume_obj = None
                        try:
                            tailored_resume_obj = _create_tailored_resume_pdf(
                                user=request.user,
                                job=job,
                                original_resume=resume,
                                tailored_text=tailored_text,
                                changes=changes,
                                keywords_added=keywords_added
                            )
                        except Exception as pdf_err:
                            logger.warning(f"PDF generation/upload failed (non-fatal) for {job.title}: {str(pdf_err)}")

                        # Link queue item to TailoredResume if PDF was generated
                        if tailored_resume_obj:
                            queue_item.tailored_resume = tailored_resume_obj
                        queue_item.cover_letter = tailored_text

                        # Mark DONE - tailoring itself succeeded regardless of PDF generation
                        queue_item.status = ApplicationQueue.Status.DONE
                        queue_item.error_message = ''
                        queue_item.save()

                        logger.info(f"Resume tailored successfully: {job.title} at {job.company}")

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'done',
                            'tailored': True,
                            'keywords_added': keywords_added,
                            'message': 'Resume tailored successfully'
                        })
                    else:
                        error_detail = tailor_response.text[:500] if tailor_response.text else "Unknown error"
                        logger.error(f"Tailoring failed for {job.title}: {error_detail}")
                        queue_item.status = ApplicationQueue.Status.FAILED
                        queue_item.error_message = f"Tailoring failed: {error_detail}"
                        queue_item.save()

                        results.append({
                            'job_id': str(job.id),
                            'queue_item_id': str(queue_item.id),
                            'title': job.title,
                            'company': job.company,
                            'status': 'failed',
                            'tailored': False,
                            'message': 'Resume tailoring failed'
                        })

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Tailoring error for {job.title}: {error_msg}")
                    import traceback
                    logger.error(traceback.format_exc())
                    try:
                        queue_item.status = ApplicationQueue.Status.FAILED
                        queue_item.error_message = f"Tailoring error: {error_msg[:500]}"
                        queue_item.save()
                    except Exception:
                        logger.error(f"Failed to update queue item status for {job.id}")

                    results.append({
                        'job_id': str(job.id),
                        'queue_item_id': str(queue_item.id),
                        'title': job.title,
                        'company': job.company,
                        'status': 'failed',
                        'tailored': False,
                        'message': error_msg
                    })

            except JobListing.DoesNotExist:
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'message': 'Job not found'
                })
            except Exception as e:
                logger.error(f"Queue error for job {job_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'message': str(e)
                })

        return Response({
            'total': len(job_ids),
            'processed': len([r for r in results if r.get('tailored')]),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'pending': len([r for r in results if r.get('status') == 'pending']),
            'results': results
        })

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get the status of all queue items for the current user"""
        queue_items = self.get_queryset().order_by('-created_at')

        serializer = self.get_serializer(queue_items, many=True)
        return Response({
            'total': queue_items.count(),
            'pending': queue_items.filter(status=ApplicationQueue.Status.QUEUED).count(),
            'processing': queue_items.filter(status=ApplicationQueue.Status.PROCESSING).count(),
            'applying': queue_items.filter(status=ApplicationQueue.Status.APPLYING).count(),
            'generating_resume': queue_items.filter(status=ApplicationQueue.Status.GENERATING_RESUME).count(),
            'done': queue_items.filter(status=ApplicationQueue.Status.DONE).count(),
            'failed': queue_items.filter(status=ApplicationQueue.Status.FAILED).count(),
            'pending_confirmation': queue_items.filter(
                status=ApplicationQueue.Status.PENDING_CONFIRMATION
            ).count(),
            'items': serializer.data
        })

    @action(detail=False, methods=['post'])
    def bulk_apply(self, request):
        """Apply to multiple jobs at once."""
        job_ids = request.data.get('job_ids', [])
        resume_id = request.data.get('resume_id')

        if not job_ids:
            return Response({
                'error': 'job_ids is required (array of job IDs)'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for job_id in job_ids:
            mini_request = type('Request', (), {
                'data': {'job_id': job_id, 'resume_id': resume_id},
                'user': request.user
            })()

            try:
                response = self.apply(mini_request)
                results.append({
                    'job_id': job_id,
                    'status': 'success' if response.status_code == 201 else 'failed',
                    'data': response.data if response.status_code == 201 else None
                })
            except Exception as e:
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'error': str(e)
                })

        return Response({
            'total': len(job_ids),
            'results': results
        })


class ApplicationViewSet(viewsets.ModelViewSet):
    """Application tracking"""
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update application status"""
        application = self.get_object()
        status_value = request.data.get('status')

        if status_value not in dict(Application.Status.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = status_value
        application.save()

        return Response({
            'id': str(application.id),
            'status': application.status,
            'message': f'Status updated to {status_value}'
        })

    @action(detail=True, methods=['post'])
    def schedule_interview(self, request, pk=None):
        """Schedule an interview"""
        application = self.get_object()
        interview_date = request.data.get('interview_date')

        if not interview_date:
            return Response(
                {'error': 'interview_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = Application.Status.INTERVIEWING
        application.interview_date = interview_date
        application.save()

        return Response({
            'id': str(application.id),
            'status': application.status,
            'interview_date': application.interview_date,
            'message': 'Interview scheduled'
        })


class CoverLetterViewSet(viewsets.ModelViewSet):
    serializer_class = CoverLetterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CoverLetter.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate cover letter (Synchronous)"""
        job_id = request.data.get('job_id')
        resume_id = request.data.get('resume_id')
        tone = request.data.get('tone', 'professional')
        additional_points = request.data.get('additional_points', '')

        if not job_id:
            return Response({
                'error': 'job_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = JobListing.objects.get(id=job_id)

            if resume_id:
                resume = Resume.objects.get(id=resume_id)
            else:
                resume = request.user.get_default_resume()
                if not resume:
                    return Response({
                        'error': 'No resume found. Please upload a resume first.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Generating cover letter for: {job.title} at {job.company}")

            response = httpx.post(
                'https://delightful-education-production-cd5d.up.railway.app/api/ai/generate-cover-letter',
                #'http://localhost:8001/api/ai/generate-cover-letter',
                json={
                    'user_id': str(request.user.id),
                    'job_id': str(job.id),
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                    'tone': tone,
                    'additional_points': additional_points
                },
                timeout=60.0
            )

            if response.status_code != 200:
                return Response({
                    'error': 'Cover letter generation failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = response.json()
            cover_letter_text = data.get('cover_letter', '')

            cover_letter = CoverLetter.objects.create(
                user=request.user,
                job=job,
                content=cover_letter_text,
                tone=tone
            )

            return Response({
                'id': str(cover_letter.id),
                'content': cover_letter.content,
                'tone': cover_letter.tone,
                'job_title': job.title,
                'company': job.company,
                'message': 'Cover letter generated successfully!'
            })

        except JobListing.DoesNotExist:
            return Response({
                'error': 'Job not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Cover letter error: {str(e)}")
            return Response({
                'error': f'Cover letter generation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import httpx
import logging
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from .models import JobListing, JobSearchHistory
from .serializers import (
    JobListingSerializer,
    JobDiscoverySerializer,
    JobApplySerializer,
    JobSearchHistorySerializer
)
from resumes.models import Resume
from applications.models import Application, CoverLetter

logger = logging.getLogger(__name__)

FASTAPI_BASE_URL = "http://localhost:8001"

SOURCE_MAP = {
    'apify_linkedin': 'official',
    'apify_indeed': 'fast',
    'apify_naukri': 'multi_platform',
    'google_jobs': 'multi_platform',
    'indeed_rss': 'fast',
    'apify_linkedin_fast': 'fast',
    'apify_official': 'official',
    'apify_multi': 'multi_platform',
}

VALID_ORDER_FIELDS = [
    'match_score', '-match_score', 'created_at', '-created_at',
    'discovered_at', '-discovered_at', 'salary_min', '-salary_min',
    'salary_max', '-salary_max', 'title', '-title',
    'company', '-company', 'is_applied', '-is_applied', 'is_saved', '-is_saved',
]


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _paginate_queryset(queryset, request, page_size_default=20, page_size_max=100):
    """
    Paginate a queryset based on request query params.
    Returns a dict suitable for Response(data).
    """
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', page_size_default))
    if page_size > page_size_max:
        page_size = page_size_max

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return {
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'page_size': page_size,
    }, page_obj


def _call_fastapi_discover(job_titles, location, max_jobs, sources, days_back=30):
    """
    Call FastAPI job discovery endpoint.
    Returns (discovered_jobs_list, fastapi_url) on success.
    Raises appropriate exceptions on failure.
    """
    fastapi_url = f"{FASTAPI_BASE_URL}/api/jobs/discover"
    translated_sources = [SOURCE_MAP.get(s, s) for s in (sources or [])]

    response = httpx.post(
        fastapi_url,
        json={
            'job_titles': job_titles,
            'location': location,
            'max_jobs': max_jobs,
            'sources': translated_sources,
            'days_back': days_back,
        },
        timeout=120.0,
    )
    if response.status_code != 200:
        logger.error(f"FastAPI error: {response.text}")
        raise Exception(f"Job discovery failed: {response.text}")

    discovered_jobs = response.json().get('jobs', [])
    logger.info(f"Found {len(discovered_jobs)} jobs from FastAPI")
    return discovered_jobs, fastapi_url


def _build_job_defaults(job_data, location, remote_only):
    """
    Build a complete defaults dict from a raw job_data dict
    for use with JobListing.objects.update_or_create().
    """
    job_url = (
        job_data.get('url')
        or job_data.get('jobUrl')
        or job_data.get('apply_url')
        or job_data.get('applyUrl')
        or job_data.get('link')
        or ''
    ).strip()

    return {
        'title': job_data.get('title', 'Unknown'),
        'company': job_data.get('company', 'Unknown'),
        'source': job_data.get('source', 'unknown'),
        'source_display': job_data.get('source_display', ''),
        'external_id': job_data.get('external_id', ''),
        'apply_url': job_data.get('apply_url', job_url),
        'location': job_data.get('location', location),
        'description': job_data.get('description') or job_data.get('descriptionText') or '',
        'salary': job_data.get('salary') or '',
        'salary_min': job_data.get('salary_min'),
        'salary_max': job_data.get('salary_max'),
        'salary_currency': job_data.get('salary_currency') or 'USD',
        'posted_date': job_data.get('posted_date'),
        'is_remote': job_data.get('is_remote', remote_only),
        'is_active': True,
        'is_saved': False,
        'status': 'discovered',
        'company_logo': job_data.get('company_logo_url') or '',
        'employment_type': job_data.get('employment_type', ''),
        'experience_required': (
            job_data.get('experience_level')
            or job_data.get('experience_required')
            or ''
        ),
        'company_website': job_data.get('company_website') or job_data.get('companyWebsite'),
        'company_slogan': job_data.get('company_slogan') or job_data.get('companySlogan') or '',
        'company_description': job_data.get('company_description') or job_data.get('companyDescription') or '',
        'employees_count': (
            job_data.get('employees_count')
            if job_data.get('employees_count') is not None
            else job_data.get('company_employees_count')
            if job_data.get('company_employees_count') is not None
            else job_data.get('companyEmployeesCount')
        ),
        'company_linkedin_url': job_data.get('company_linkedin_url') or job_data.get('companyLinkedinUrl'),
    }


def _extract_job_url(job_data):
    """Extract a valid job URL from various possible fields."""
    url = (
        job_data.get('url')
        or job_data.get('jobUrl')
        or ''
    ).strip()
    if not url:
        url = (
            job_data.get('apply_url')
            or job_data.get('applyUrl')
            or job_data.get('link')
            or ''
        ).strip()
    if not url:
        ext_id = (job_data.get('external_id') or job_data.get('id') or '').strip()
        if ext_id.startswith('http://') or ext_id.startswith('https://'):
            url = ext_id
    return url


def _save_discovered_jobs(discovered_jobs, user, location, remote_only):
    """
    Save discovered jobs to the database.
    Returns (saved_jobs_list, new_job_ids_list, errors_list).
    """
    saved_jobs = []
    new_jobs = []
    errors = []

    for idx, job_data in enumerate(discovered_jobs):
        try:
            job_url = _extract_job_url(job_data)
            if not job_url or not (job_url.startswith('http://') or job_url.startswith('https://')):
                logger.warning(f"Job {idx + 1} has invalid URL, skipping.")
                continue

            defaults = _build_job_defaults(job_data, location, remote_only)
            job, created = JobListing.objects.update_or_create(
                url=job_url, user=user, defaults=defaults
            )
            saved_jobs.append({
                'id': str(job.id),
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'source': job.source,
                'is_new': created,
                'match_score': job.match_score,
            })
            if created:
                new_jobs.append(str(job.id))
        except Exception as e:
            errors.append(f"Job {idx + 1}: {str(e)}")

    return saved_jobs, new_jobs, errors


def _build_resume_match_text(resume):
    """Return the best available text to score a resume when parsed_text is unavailable."""
    if not resume:
        return ""

    if resume.parsed_text and resume.parsed_text.strip():
        return resume.parsed_text

    parts = []

    for value in [
        resume.extracted_skills,
        resume.extracted_job_titles,
        getattr(resume.user, 'preferred_job_titles', []),
        getattr(resume.user, 'skills', []),
        getattr(resume.user, 'professional_summary', ''),
    ]:
        if not value:
            continue
        if isinstance(value, str):
            clean = value.strip()
            if clean:
                parts.append(clean)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    parts.append(item.strip())

    if not parts:
        return ""

    return " ".join(dict.fromkeys(parts))



def _batch_match_jobs(job_ids, user, resume):
    """
    Batch-match new jobs against a user's resume via FastAPI AI.
    Uses Gemini AI model (same as tailor_resume for consistency).
    Returns the number of successfully matched jobs.
    """
    if not job_ids or not resume:
        logger.warning(f"Skipping batch matching: job_ids={bool(job_ids)}, resume={bool(resume)}")
        return 0

    resume_text = _build_resume_match_text(resume)
    if not resume_text:
        logger.warning(f"Skipping batch matching for user {user.id}: no resume text or extracted skills available")
        return 0

    logger.info(f"Starting batch match for user {user.id}, resume {resume.id}, jobs: {job_ids}")
    matched_count = 0
    try:
        # Fetch job details from DB to send directly to FastAPI
        jobs_qs = JobListing.objects.filter(id__in=job_ids).values(
            'id', 'title', 'description', 'company'
        )
        jobs_data = [
            {
                'job_id': str(j['id']),
                'title': j['title'] or '',
                'description': j['description'] or '',
                'company': j['company'] or '',
            }
            for j in jobs_qs
        ]

        if not jobs_data:
            logger.warning(f"No jobs found in database for IDs: {job_ids}")
            return 0

        logger.info(f"Calling FastAPI batch-match endpoint: {FASTAPI_BASE_URL}/api/ai/batch-match with {len(jobs_data)} jobs")
        
        # Call FastAPI AI batch-match endpoint
        response = httpx.post(
            f"{FASTAPI_BASE_URL}/api/ai/batch-match",
            json={
                'user_id': str(user.id),
                'resume_id': str(resume.id),
                'resume_text': resume_text,
                'job_ids': job_ids,
                'jobs': jobs_data,
            },
            timeout=180.0,
        )

        logger.info(f"FastAPI response status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            logger.info(f"Received {len(results)} match results from FastAPI")
            
            # Process AI results
            for result in results:
                jid = result.get('job_id')
                match_score = result.get('match_score')
                if jid:
                    logger.info(f"Updating job {jid} with match_score={match_score}")
                    JobListing.objects.filter(id=jid).update(
                        match_score=result.get('match_score', 0),
                        missing_skills=result.get('missing_skills', []),
                        fit_analysis=result.get('fit_analysis', ''),
                        strengths=result.get('strengths', []),
                        recommended_keywords=result.get('recommended_keywords', []),
                    )
                    matched_count += 1
        else:
            response_text = response.text[:500]  # First 500 chars
            logger.error(f"AI batch-match failed with status {response.status_code}: {response_text}")
            # Mark jobs as processed but with 0 score if AI fails
            for jid in job_ids:
                JobListing.objects.filter(id=jid).update(
                    match_score=0,
                    fit_analysis='AI match analysis unavailable - service error.',
                )
                matched_count += 1

    except httpx.TimeoutException as e:
        logger.error(f"AI batch-match timed out for user {user.id}: {str(e)}")
        # Mark jobs as processed but with 0 score on timeout
        for jid in job_ids:
            JobListing.objects.filter(id=jid).update(
                match_score=0,
                fit_analysis='AI match analysis timed out.',
            )
            matched_count += len(job_ids)

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to FastAPI service at {FASTAPI_BASE_URL}: {str(e)}")
        # Mark jobs as processed but with 0 score if service is unavailable
        for jid in job_ids:
            JobListing.objects.filter(id=jid).update(
                match_score=0,
                fit_analysis=f'FastAPI AI service unavailable at {FASTAPI_BASE_URL}',
            )
            matched_count += len(job_ids)

    except Exception as e:
        logger.error(f"Batch matching failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Mark jobs as processed but with 0 score if any other error
        for jid in job_ids:
            JobListing.objects.filter(id=jid).update(
                match_score=0,
                fit_analysis=f'AI match analysis failed: {str(e)[:100]}',
            )
            matched_count += len(job_ids)

    logger.info(f"Batch match completed: {matched_count} jobs matched")
    return matched_count


def _build_discover_response_data(discovered_jobs, saved_jobs, new_jobs, matched_count,
                                    job_titles, location, from_resume=False, errors=None):
    """Build a standard response for discover/auto_discover actions."""
    return {
        'status': 'success',
        'jobs_found': len(discovered_jobs),
        'jobs_saved': len(saved_jobs),
        'new_jobs': len(new_jobs),
        'matched_count': matched_count,
        'job_titles_used': job_titles,
        'location_used': location,
        'from_resume': from_resume,
        'errors': errors if errors else None,
        'jobs': saved_jobs,
        'message': (
            f'Found {len(discovered_jobs)} jobs. '
            f'Saved {len(saved_jobs)} jobs. '
            f'Matched {matched_count} jobs.'
        ),
    }


# =============================================================================
# VIEWSET
# =============================================================================

class JobListingViewSet(viewsets.ModelViewSet):
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source', 'status', 'is_applied', 'is_saved', 'is_remote']

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return JobListing.objects.none()

        queryset = JobListing.objects.filter(user=self.request.user)
        params = self.request.query_params

        # Advanced filters beyond DjangoFilterBackend fields
        min_score = params.get('min_score')
        if min_score:
            queryset = queryset.filter(match_score__gte=float(min_score))

        max_score = params.get('max_score')
        if max_score:
            queryset = queryset.filter(match_score__lte=float(max_score))

        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(company__icontains=search)
                | Q(location__icontains=search)
            )

        min_salary = params.get('min_salary')
        if min_salary:
            queryset = queryset.filter(
                Q(salary_min__gte=float(min_salary))
                | Q(salary_max__gte=float(min_salary))
            )

        max_salary = params.get('max_salary')
        if max_salary:
            queryset = queryset.filter(
                Q(salary_max__lte=float(max_salary))
                | Q(salary_min__lte=float(max_salary))
            )

        date_from = params.get('date_from')
        if date_from:
            queryset = queryset.filter(discovered_at__gte=date_from)

        date_to = params.get('date_to')
        if date_to:
            queryset = queryset.filter(discovered_at__lte=date_to)

        company = params.get('company')
        if company:
            queryset = queryset.filter(company__icontains=company)

        location = params.get('location')
        if location and location.lower() != 'all locations':
            queryset = queryset.filter(location__icontains=location)

        title = params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        ordering = params.get('ordering', '-match_score')
        if ordering in VALID_ORDER_FIELDS:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-match_score', '-discovered_at')

        return queryset

   

    @action(detail=False, methods=['get'])
    def saved(self, request):
        try:
            jobs = JobListing.objects.filter(
                user=request.user, is_saved=True, is_active=True
            ).order_by('-match_score', '-saved_at')
            pagination_data, page_obj = _paginate_queryset(jobs, request)
            serializer = self.get_serializer(page_obj, many=True)
            return Response({
                'status': 'success',
                **pagination_data,
                'results': serializer.data,
            })
        except Exception as e:
            logger.error(f"Error in saved: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def applied(self, request):
        try:
            jobs = JobListing.objects.filter(
                user=request.user, is_applied=True, is_active=True
            ).order_by('-applied_at')
            pagination_data, page_obj = _paginate_queryset(jobs, request)
            serializer = self.get_serializer(page_obj, many=True)
            return Response({
                'status': 'success',
                **pagination_data,
                'results': serializer.data,
            })
        except Exception as e:
            logger.error(f"Error in applied: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def matched(self, request):
        try:
            jobs = JobListing.objects.filter(
                user=request.user, match_score__isnull=False, is_active=True
            ).order_by('-match_score')

            min_score = request.query_params.get('min_score')
            if min_score:
                jobs = jobs.filter(match_score__gte=float(min_score))

            pagination_data, page_obj = _paginate_queryset(jobs, request)
            serializer = self.get_serializer(page_obj, many=True)
            return Response({
                'status': 'success',
                **pagination_data,
                'results': serializer.data,
            })
        except Exception as e:
            logger.error(f"Error in matched: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            jobs = JobListing.objects.filter(user=request.user)
            stats_data = {
                'total': jobs.count(),
                'active': jobs.filter(is_active=True).count(),
                'saved': jobs.filter(is_saved=True).count(),
                'applied': jobs.filter(is_applied=True).count(),
                'pending': jobs.filter(is_saved=True, is_applied=False).count(),
                'matched': jobs.filter(match_score__isnull=False).count(),
                'by_source': {},
                'by_status': {},
                'match_score': {
                    'average': (
                        jobs.filter(match_score__isnull=False).aggregate(Avg('match_score'))['match_score__avg']
                        or 0
                    ),
                    'high': jobs.filter(match_score__gte=80).count(),
                    'medium': jobs.filter(match_score__gte=60, match_score__lt=80).count(),
                    'low': jobs.filter(match_score__lt=60).count(),
                    'unmatched': jobs.filter(match_score__isnull=True).count(),
                },
                'top_companies': list(
                    jobs.values('company')
                    .annotate(count=Count('id'))
                    .order_by('-count')[:10]
                ),
                'top_titles': list(
                    jobs.values('title')
                    .annotate(count=Count('id'))
                    .order_by('-count')[:10]
                ),
            }

            for source in jobs.values_list('source', flat=True).distinct():
                stats_data['by_source'][source] = jobs.filter(source=source).count()
            for status_choice in JobListing.Status.choices:
                stats_data['by_status'][status_choice[0]] = jobs.filter(status=status_choice[0]).count()

            return Response(stats_data)

        except Exception as e:
            logger.error(f"Error in stats: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =========================================================================
    # JOB DISCOVERY
    # =========================================================================

    @action(detail=False, methods=['post'], url_path='discover')
    def discover(self, request):
        serializer = JobDiscoverySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = request.user
            preferences = user.preferences
            validated = serializer.validated_data

            job_titles = validated.get('job_titles', preferences.get('job_titles', ['Software Engineer']))
            location = validated.get('location', 'United States')
            max_jobs = validated.get('max_jobs', 30)
            sources = validated.get('sources', ['google_jobs', 'indeed_rss'])
            remote_only = validated.get('remote_only', False)

            logger.info(f"Discovering jobs for user: {user.id}, titles={job_titles}, location={location}")

            # Call FastAPI discovery service
            try:
                discovered_jobs, fastapi_url = _call_fastapi_discover(
                    job_titles, location, max_jobs, sources, days_back=30
                )
            except httpx.TimeoutException:
                return Response(
                    {'error': 'Job discovery timeout', 'fastapi_url': f"{FASTAPI_BASE_URL}/api/jobs/discover"},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )
            except httpx.ConnectError:
                return Response(
                    {
                        'error': 'Cannot connect to FastAPI service',
                        'fastapi_url': f"{FASTAPI_BASE_URL}/api/jobs/discover",
                        'message': 'Make sure FastAPI is running on port 8001',
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except Exception as e:
                return Response(
                    {'error': f'Job discovery failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save discovered jobs
            saved_jobs, new_jobs, errors = _save_discovered_jobs(
                discovered_jobs, user, location, remote_only
            )

            # Batch-match new jobs
            resume = user.get_default_resume()
            matched_count = _batch_match_jobs(new_jobs, user, resume)

            # Save search history
            try:
                JobSearchHistory.objects.create(
                    user=user,
                    keywords=job_titles,
                    location=location,
                    sources=sources,
                    jobs_found=len(discovered_jobs),
                    jobs_saved=len(saved_jobs),
                    search_params=serializer.validated_data,
                )
            except Exception as e:
                logger.warning(f"Failed to save search history: {str(e)}")

            response_data = _build_discover_response_data(
                discovered_jobs, saved_jobs, new_jobs, matched_count,
                job_titles, location, errors=errors,
            )
            response_data['fastapi_url'] = fastapi_url
            return Response(response_data)

        except Exception as e:
            logger.error(f"Discovery error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Discovery failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], url_path='auto_discover')
    def auto_discover(self, request):
        try:
            user = request.user
            location = "Remote"
            max_jobs = 50
            sources = ['apify_linkedin', 'apify_indeed', 'apify_naukri']
            remote_only = False
            default_resume = Resume.objects.filter(user=user, is_default=True).first()

            # Determine job titles from resume or user preferences
            if default_resume and default_resume.extracted_job_titles:
                job_titles = default_resume.extracted_job_titles
            elif user.preferred_job_titles and len(user.preferred_job_titles) > 0:
                job_titles = user.preferred_job_titles
            else:
                job_titles = [
                    "Software Engineer", "Data Scientist", "Product Manager",
                    "Marketing Specialist", "Graphic Designer", "Business Analyst",
                    "Sales Representative", "Customer Success Manager",
                    "DevOps Engineer", "UX Designer", "Financial Analyst",
                    "HR Manager", "Content Writer", "Project Manager",
                    "Mechanical Engineer",
                ]

            if user.preferred_locations and len(user.preferred_locations) > 0:
                location = ", ".join(user.preferred_locations)

            logger.info(f"Auto-discovering for user: {user.id}, titles={job_titles}")

            # Call FastAPI discovery service
            try:
                discovered_jobs, _ = _call_fastapi_discover(
                    job_titles, location, max_jobs, sources, days_back=7
                )
            except httpx.TimeoutException:
                return Response(
                    {'status': 'error', 'message': 'Auto discovery timeout'},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )
            except httpx.ConnectError:
                return Response(
                    {'status': 'error', 'message': 'FastAPI service unavailable'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except Exception as e:
                return Response(
                    {'status': 'error', 'message': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save discovered jobs
            saved_jobs, new_jobs, errors = _save_discovered_jobs(
                discovered_jobs, user, location, remote_only
            )

            # Batch-match new jobs
            matched_count = _batch_match_jobs(new_jobs, user, default_resume)

            # Save search history
            try:
                JobSearchHistory.objects.create(
                    user=user,
                    keywords=job_titles,
                    location=location,
                    sources=sources,
                    jobs_found=len(discovered_jobs),
                    jobs_saved=len(saved_jobs),
                    search_params={'auto_discover': True},
                )
            except Exception:
                pass

            response_data = _build_discover_response_data(
                discovered_jobs, saved_jobs, new_jobs, matched_count,
                job_titles, location, from_resume=default_resume is not None, errors=errors,
            )
            response_data['auto_discovered'] = True
            return Response(response_data)

        except Exception as e:
            logger.error(f"Auto-discover error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'status': 'error', 'message': f'Auto-discover failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =========================================================================
    # JOB APPLICATION
    # =========================================================================

    @action(detail=False, methods=['post'])
    def apply(self, request):
        serializer = JobApplySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        job_id = serializer.validated_data['job_id']
        resume_id = serializer.validated_data.get('resume_id')
        tone = serializer.validated_data.get('tone', 'professional')

        try:
            job = JobListing.objects.get(id=job_id, user=request.user)

            if resume_id:
                resume = Resume.objects.get(id=resume_id, user=request.user)
            else:
                resume = request.user.get_default_resume()
                if not resume:
                    return Response(
                        {'error': 'No resume found. Please upload a resume first.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            logger.info(f"Applying to: {job.title} at {job.company} using resume: {resume.name}")

            # Tailor resume
            logger.info("Tailoring resume...")
            tailoring_result = self._tailor_resume(resume, job)

            # Generate cover letter
            logger.info("Generating cover letter...")
            cover_letter_result = self._generate_cover_letter(resume, job, tone)

            # Submit application
            logger.info("Submitting application...")
            submission_result = self._submit_application(
                request.user, job,
                tailoring_result['tailored_resume'],
                cover_letter_result['cover_letter'],
            )

            # Save application record
            logger.info("Saving application record...")
            application = Application.objects.create(
                user=request.user,
                job=job,
                resume=tailoring_result['tailored_resume'],
                cover_letter=cover_letter_result['cover_letter'],
                status=Application.Status.APPLIED,
                application_url=job.apply_url or job.url,
                applied_at=timezone.now(),
            )

            job.is_applied = True
            job.is_saved = True
            job.status = JobListing.Status.APPLIED
            job.applied_at = timezone.now()
            job.save()

            cover_letter_result['cover_letter_obj'].is_used = True
            cover_letter_result['cover_letter_obj'].save()

            return Response(
                {
                    'status': 'success',
                    'job_title': job.title,
                    'company': job.company,
                    'application_id': str(application.id),
                    'application_status': application.status,
                    'application_url': application.application_url,
                    'message': 'Application submitted successfully!',
                    'tailored_resume_id': str(tailoring_result['tailored_resume'].id),
                    'cover_letter_id': str(cover_letter_result['cover_letter_obj'].id),
                    'match_score': job.match_score,
                },
                status=status.HTTP_201_CREATED,
            )

        except JobListing.DoesNotExist:
            return Response(
                {'error': 'Job not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Resume.DoesNotExist:
            return Response(
                {'error': 'Resume not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Application failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'])
    def bulk_apply(self, request):
        job_ids = request.data.get('job_ids', [])
        resume_id = request.data.get('resume_id')

        if not job_ids:
            return Response(
                {'error': 'job_ids is required (array of job IDs)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        for job_id in job_ids:
            try:
                mini_request = type('Request', (), {
                    'data': {'job_id': job_id, 'resume_id': resume_id},
                    'user': request.user,
                })()
                response = self.apply(mini_request)

                if response.status_code == 201:
                    results.append({
                        'job_id': job_id,
                        'status': 'success',
                        'data': response.data,
                    })
                else:
                    results.append({
                        'job_id': job_id,
                        'status': 'failed',
                        'error': response.data.get('error', 'Unknown error'),
                    })
            except Exception as e:
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'error': str(e),
                })

        return Response({
            'total': len(job_ids),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'results': results,
        })

    # =========================================================================
    # SAVE / UNSAVE
    # =========================================================================

    @action(detail=True, methods=['post'])
    def save_job(self, request, pk=None):
        try:
            job = self.get_object()
            job.is_saved = True
            job.user = request.user
            if not job.saved_at:
                job.saved_at = timezone.now()
            job.save()
            return Response({
                'status': 'success',
                'message': 'Job saved successfully',
                'job_id': str(job.id),
                'is_saved': True,
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def unsave_job(self, request, pk=None):
        try:
            job = self.get_object()
            job.is_saved = False
            job.saved_at = None
            job.save()
            return Response({
                'status': 'success',
                'message': 'Job removed from saved list',
                'job_id': str(job.id),
                'is_saved': False,
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =========================================================================
    # SEARCH HISTORY
    # =========================================================================

    @action(detail=False, methods=['get'])
    def search_history(self, request):
        try:
            history = JobSearchHistory.objects.filter(
                user=request.user
            ).order_by('-created_at')[:20]
            serializer = JobSearchHistorySerializer(history, many=True)
            return Response({
                'status': 'success',
                'results': serializer.data,
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _tailor_resume(self, resume, job):
        """Tailor resume for a specific job via FastAPI."""
        try:
            response = httpx.post(
                f'{FASTAPI_BASE_URL}/api/resumes/tailor',
                json={
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                },
                timeout=180.0,
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
                is_default=False,
                is_tailored=True,
                tailored_for_job=job,
                tailored_from=resume,
                changes_summary=data.get('changes', {}),
                version=resume.version + 1,
            )
            return {
                'tailored_resume': tailored_resume,
                'changes': data.get('changes', {}),
            }
        except Exception as e:
            logger.error(f"Tailoring error: {str(e)}")
            raise

    def _generate_cover_letter(self, resume, job, tone='professional'):
        """Generate a cover letter for a job via FastAPI."""
        try:
            response = httpx.post(
                f'{FASTAPI_BASE_URL}/api/ai/generate-cover-letter',
                json={
                    'user_id': str(resume.user.id),
                    'job_id': str(job.id),
                    'resume_text': resume.parsed_text,
                    'job_description': job.description,
                    'job_title': job.title,
                    'company': job.company,
                    'tone': tone,
                    'additional_points': '',
                },
                timeout=60.0,
            )
            if response.status_code != 200:
                raise Exception(f"Cover letter generation failed: {response.text}")

            data = response.json()
            cover_letter_text = data.get('cover_letter', '')

            cover_letter = CoverLetter.objects.create(
                user=resume.user,
                job=job,
                content=cover_letter_text,
                tone=tone,
            )
            return {
                'cover_letter': cover_letter_text,
                'cover_letter_obj': cover_letter,
            }
        except Exception as e:
            logger.error(f"Cover letter error: {str(e)}")
            raise

    def _submit_application(self, user, job, tailored_resume, cover_letter):
        """Submit application via FastAPI/Playwright."""
        try:
            response = httpx.post(
                f'{FASTAPI_BASE_URL}/api/applications/submit',
                json={
                    'user_id': str(user.id),
                    'job_id': str(job.id),
                    'tailored_resume_id': str(tailored_resume.id),
                    'cover_letter': cover_letter,
                    'platform': job.source,
                    'url': job.apply_url or job.url,
                },
                timeout=120.0,
            )
            if response.status_code != 200:
                raise Exception(f"Submission failed: {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"Submission error: {str(e)}")
            raise


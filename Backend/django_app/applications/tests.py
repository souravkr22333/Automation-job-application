from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.models import Application, ApplicationQueue, CoverLetter
from applications.views import ApplicationQueueViewSet
from jobs.models import JobListing
from resumes.models import Resume, TailoredResume
from resumes.services import PDFGenerator
from resumes.tasks import tailor_resume_async
from users.models import User


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
})
class ApplicationQueueAutoGenerateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            name='Test User',
            password='StrongPass123!'
        )
        self.resume = Resume.objects.create(
            user=self.user,
            name='resume.pdf',
            supabase_url='https://example.com/resume.pdf',
            supabase_path='users/test/resume.pdf',
            supabase_bucket='resumes',
            file_size=123,
            file_type='application/pdf',
            parsed_text='Experienced Python developer',
            is_default=True,
            version=1,
        )
        self.job = JobListing.objects.create(
            user=self.user,
            title='Python Developer',
            company='Acme',
            url='https://example.com/jobs/123',
            description='We need a Python developer with Django experience.',
            source='linkedin',
        )

    @patch('applications.views.httpx.post')
    def test_auto_generate_creates_valid_tailored_resume_record(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'tailored_text': 'Tailored resume text with Python and Django.',
                'changes': {'summary': 'Added Python skills'},
                'keywords_added': ['Python', 'Django'],
            },
            text='ok',
        )

        factory = APIRequestFactory()
        request = factory.post(
            '/api/queue/auto_generate/',
            {'job_ids': [str(self.job.id)]},
            format='json',
        )
        force_authenticate(request, self.user)

        response = ApplicationQueueViewSet.as_view({'post': 'auto_generate'})(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ApplicationQueue.objects.filter(user=self.user, job=self.job).exists())
        self.assertTrue(TailoredResume.objects.filter(user=self.user, job=self.job).exists())

    @patch('applications.views.httpx.post')
    def test_auto_apply_enforces_daily_limit(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'tailored_text': 'Tailored resume text with Python and Django.',
                'changes': {'summary': 'Added Python skills'},
                'keywords_added': ['Python', 'Django'],
            },
            text='ok',
        )

        for _ in range(10):
            Application.objects.create(
                user=self.user,
                job=self.job,
                resume=self.resume,
                cover_letter='test',
                status='applied',
                application_url='https://example.com/apply',
            )

        factory = APIRequestFactory()
        request = factory.post(
            '/api/queue/auto_apply/',
            {'job_ids': [str(self.job.id)]},
            format='json',
        )
        force_authenticate(request, self.user)

        response = ApplicationQueueViewSet.as_view({'post': 'auto_apply'})(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn('10', response.data.get('detail', ''))

    def test_auto_apply_records_only_confirmed_submissions(self):
        tailored_pdf = TailoredResume.objects.create(
            user=self.user,
            job=self.job,
            original_resume=self.resume,
            name='tailored.pdf',
            supabase_url='https://storage.example.com/tailored.pdf',
            supabase_path='users/test/tailored.pdf',
            supabase_bucket='Tailored resume',
            file_size=456,
            file_type='application/pdf',
            tailored_text='Tailored resume text',
        )
        cover_letter = CoverLetter.objects.create(
            user=self.user,
            job=self.job,
            content='A tailored cover letter',
        )
        with patch.object(
            ApplicationQueueViewSet,
            '_tailor_resume',
            return_value={'tailored_resume': self.resume, 'changes': {}},
        ), patch(
            'applications.views._create_tailored_resume_pdf',
            return_value=tailored_pdf,
        ), patch.object(
            ApplicationQueueViewSet,
            '_generate_cover_letter',
            return_value={'cover_letter': cover_letter.content, 'cover_letter_obj': cover_letter},
        ), patch.object(
            ApplicationQueueViewSet,
            '_submit_application',
            return_value={
                'status': 'success',
                'application_url': 'https://example.com/confirmation',
                'message': 'Application submitted successfully',
            },
        ):
            factory = APIRequestFactory()
            request = factory.post(
                '/api/applications/queue/auto_apply/',
                {'job_ids': [str(self.job.id)]},
                format='json',
            )
            force_authenticate(request, self.user)
            response = ApplicationQueueViewSet.as_view({'post': 'auto_apply'})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['status'], 'applied')
        application = Application.objects.get(user=self.user, job=self.job)
        self.assertEqual(application.application_url, 'https://example.com/confirmation')
        queue_item = ApplicationQueue.objects.get(user=self.user, job=self.job)
        self.assertEqual(queue_item.status, ApplicationQueue.Status.DONE)
        self.assertEqual(queue_item.tailored_resume, tailored_pdf)

    def test_auto_apply_keeps_unconfirmed_submission_pending(self):
        tailored_pdf = TailoredResume.objects.create(
            user=self.user,
            job=self.job,
            original_resume=self.resume,
            name='tailored.pdf',
            supabase_url='https://storage.example.com/tailored.pdf',
            supabase_path='users/test/tailored.pdf',
            supabase_bucket='Tailored resume',
            file_size=456,
            file_type='application/pdf',
            tailored_text='Tailored resume text',
        )
        cover_letter = CoverLetter.objects.create(
            user=self.user,
            job=self.job,
            content='A tailored cover letter',
        )
        with patch.object(
            ApplicationQueueViewSet,
            '_tailor_resume',
            return_value={'tailored_resume': self.resume, 'changes': {}},
        ), patch(
            'applications.views._create_tailored_resume_pdf',
            return_value=tailored_pdf,
        ), patch.object(
            ApplicationQueueViewSet,
            '_generate_cover_letter',
            return_value={'cover_letter': cover_letter.content, 'cover_letter_obj': cover_letter},
        ), patch.object(
            ApplicationQueueViewSet,
            '_submit_application',
            return_value={
                'status': 'pending_confirmation',
                'application_url': 'https://example.com/apply',
                'message': 'Submission could not be confirmed',
            },
        ):
            factory = APIRequestFactory()
            request = factory.post(
                '/api/applications/queue/auto_apply/',
                {'job_ids': [str(self.job.id)]},
                format='json',
            )
            force_authenticate(request, self.user)
            response = ApplicationQueueViewSet.as_view({'post': 'auto_apply'})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['status'], 'pending_confirmation')
        self.assertFalse(Application.objects.filter(user=self.user, job=self.job).exists())
        queue_item = ApplicationQueue.objects.get(user=self.user, job=self.job)
        self.assertEqual(queue_item.status, ApplicationQueue.Status.PENDING_CONFIRMATION)

    @override_settings(
        FASTAPI_BASE_URL='http://fastapi:8001',
        FASTAPI_INTERNAL_TOKEN='test-internal-token',
    )
    @patch('applications.views.httpx.post')
    def test_submission_request_uses_internal_contract(self, mock_post):
        queue_item = ApplicationQueue.objects.create(
            user=self.user,
            job=self.job,
            idempotency_key='test-auto-apply',
        )
        tailored_pdf = TailoredResume.objects.create(
            user=self.user,
            job=self.job,
            original_resume=self.resume,
            name='tailored.pdf',
            supabase_url='https://storage.example.com/tailored.pdf',
            supabase_path='users/test/tailored.pdf',
            supabase_bucket='Tailored resume',
            file_size=456,
            file_type='application/pdf',
            tailored_text='Tailored resume text',
        )
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'status': 'success',
                'application_url': 'https://example.com/confirmation',
                'message': 'Submitted',
            },
            text='ok',
        )

        result = ApplicationQueueViewSet()._submit_application(
            self.user,
            self.job,
            queue_item,
            tailored_pdf,
            'Cover letter text',
        )

        self.assertEqual(result['status'], 'success')
        request_kwargs = mock_post.call_args.kwargs
        self.assertEqual(
            request_kwargs['json']['resume_url'],
            tailored_pdf.supabase_url,
        )
        self.assertEqual(request_kwargs['json']['queue_item_id'], str(queue_item.id))
        self.assertEqual(
            request_kwargs['headers']['X-Internal-Token'],
            'test-internal-token',
        )

    def test_generate_resume_pdf_returns_valid_pdf_bytes(self):
        pdf_bytes = PDFGenerator.generate_resume_pdf(
            'SUMMARY:\n- Python Developer with Django experience\nEXPERIENCE:\n- Built APIs',
            'Test Resume'
        )

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertGreater(len(pdf_bytes), 100)

    @patch('resumes.tasks.httpx.Client')
    def test_tailor_resume_async_uses_sync_httpx_client(self, mock_client):
        mock_response = Mock(
            status_code=200,
            json=lambda: {
                'tailored_text': 'Tailored resume text with Python and Django.',
                'changes': {'summary': 'Added Python skills'},
                'keywords_added': ['Python', 'Django'],
            },
            text='ok',
        )
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = tailor_resume_async.run(str(self.resume.id), str(self.job.id))

        self.assertEqual(result['status'], 'tailored')
        self.assertIn('resume_id', result)
        self.assertTrue(Resume.objects.filter(user=self.user, tailored_for_job=self.job).exists())

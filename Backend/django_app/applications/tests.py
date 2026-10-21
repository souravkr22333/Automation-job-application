from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from applications.models import Application, ApplicationQueue
from applications.views import ApplicationQueueViewSet
from jobs.models import JobListing
from resumes.models import Resume, TailoredResume
from resumes.services import PDFGenerator
from resumes.tasks import tailor_resume_async
from users.models import User


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

from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model

from jobs.models import JobListing
from jobs.views import _batch_match_jobs
from resumes.models import Resume


class BatchMatchAITests(TestCase):
    def test_batch_match_uses_ai_service_for_scoring(self):
        """Verify that batch matching uses AI service for scoring."""
        User = get_user_model()
        user = User.objects.create_user(
            username='matcher',
            email='matcher@example.com',
            password='StrongPass123!',
            name='Matcher User',
        )

        resume = Resume.objects.create(
            user=user,
            name='resume.pdf',
            supabase_url='https://example.com/resume.pdf',
            supabase_path='user/resume.pdf',
            file_size=1024,
            file_type='application/pdf',
            parsed_text='Experienced Python and Django developer with 5 years of experience.',
            extracted_skills=['Python', 'Django', 'React'],
            extracted_job_titles=['Python Developer'],
            is_default=True,
        )

        job = JobListing.objects.create(
            user=user,
            url='https://example.com/jobs/python-django-developer',
            title='Python Developer',
            company='Acme Labs',
            description='Need Python Django and React experience for backend and frontend work.',
            location='Remote',
        )

        # Mock successful AI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'job_id': str(job.id),
                    'match_score': 85,
                    'missing_skills': ['Kubernetes', 'Docker'],
                    'fit_analysis': 'Strong match - candidate has core Python and Django skills.',
                    'strengths': ['Python expertise', 'Backend development', 'Problem solving'],
                    'recommended_keywords': ['DevOps', 'CI/CD'],
                }
            ]
        }

        with patch('jobs.views.httpx.post', return_value=mock_response) as mock_post:
            matched_count = _batch_match_jobs([str(job.id)], user, resume)

        job.refresh_from_db()

        self.assertEqual(matched_count, 1)
        self.assertEqual(job.match_score, 85)
        self.assertEqual(job.missing_skills, ['Kubernetes', 'Docker'])
        self.assertIn('Strong match', job.fit_analysis)
        self.assertEqual(job.strengths, ['Python expertise', 'Backend development', 'Problem solving'])
        self.assertEqual(job.recommended_keywords, ['DevOps', 'CI/CD'])

    def test_batch_match_sets_zero_score_on_ai_failure(self):
        """Verify that jobs get 0 score if AI service fails."""
        User = get_user_model()
        user = User.objects.create_user(
            username='matcher2',
            email='matcher2@example.com',
            password='StrongPass123!',
            name='Matcher User 2',
        )

        resume = Resume.objects.create(
            user=user,
            name='resume2.pdf',
            supabase_url='https://example.com/resume2.pdf',
            supabase_path='user/resume2.pdf',
            file_size=1024,
            file_type='application/pdf',
            parsed_text='Some experience',
            extracted_skills=['Python'],
            is_default=True,
        )

        job = JobListing.objects.create(
            user=user,
            url='https://example.com/jobs/test-job',
            title='Test Job',
            company='Test Company',
            description='Test description.',
            location='Remote',
        )

        # Mock AI service failure
        with patch('jobs.views.httpx.post') as mock_post:
            mock_post.side_effect = Exception('AI service unavailable')
            matched_count = _batch_match_jobs([str(job.id)], user, resume)

        job.refresh_from_db()

        self.assertEqual(matched_count, 1)
        self.assertEqual(job.match_score, 0)
        self.assertIn('failed', job.fit_analysis.lower())


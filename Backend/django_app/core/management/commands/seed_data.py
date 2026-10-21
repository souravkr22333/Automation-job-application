# backend/django_app/core/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.timezone import now
import uuid
import random

from users.models import User
from resumes.models import Resume
from jobs.models import JobListing
from applications.models import ApplicationQueue, Application

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with test data'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        # Create test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'name': 'Test User',
                'is_active': True
            }
        )
        if created:
            user.set_password('testpassword123')
            user.save()
            self.stdout.write(f'Created test user: {user.email}')
        
        # Create sample resume
        resume, created = Resume.objects.get_or_create(
            user=user,
            name='My Resume',
            defaults={
                'file_url': 'https://example.com/resume.pdf',
                'parsed_text': 'Experienced software engineer with 5 years of experience...',
                'extracted_skills': ['Python', 'React', 'Django', 'PostgreSQL'],
                'extracted_experience': 5,
                'is_default': True
            }
        )
        self.stdout.write(f'Created resume: {resume.name}')
        
        # Create sample jobs
        jobs_data = [
            {
                'title': 'Senior React Developer',
                'company': 'Google',
                'description': 'Build amazing web applications with React and TypeScript...',
                'url': 'https://linkedin.com/jobs/1',
                'source': 'linkedin',
                'location': 'Remote',
                'match_score': 85,
                'is_active': True
            },
            {
                'title': 'Backend Engineer (Python)',
                'company': 'Amazon',
                'description': 'Design and build scalable backend services...',
                'url': 'https://linkedin.com/jobs/2',
                'source': 'linkedin',
                'location': 'Seattle, WA',
                'match_score': 75,
                'is_active': True
            },
            {
                'title': 'Full Stack Developer',
                'company': 'Microsoft',
                'description': 'Full stack development with React and .NET...',
                'url': 'https://indeed.com/jobs/3',
                'source': 'indeed',
                'location': 'Remote',
                'match_score': 65,
                'is_active': True
            },
        ]
        
        for job_data in jobs_data:
            job, created = JobListing.objects.get_or_create(
                url=job_data['url'],
                source=job_data['source'],
                defaults=job_data
            )
            if created:
                self.stdout.write(f'Created job: {job.title} at {job.company}')
        
        # Create sample applications
        for job in JobListing.objects.all():
            app, created = Application.objects.get_or_create(
                user=user,
                job=job,
                defaults={
                    'resume': resume,
                    'cover_letter': 'I am very excited to apply for this position...',
                    'status': random.choice(['applied', 'interviewing', 'rejected']),
                    'applied_at': now()
                }
            )
            if created:
                self.stdout.write(f'Created application: {app.job.title}')
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
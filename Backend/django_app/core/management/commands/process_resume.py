# Create a management command
# backend/django_app/core/management/commands/process_resume.py
from django.core.management.base import BaseCommand
from resumes.models import Resume
from resumes.services import ResumeParser
from django.core.files.storage import default_storage

class Command(BaseCommand):
    help = 'Process a resume manually'

    def add_arguments(self, parser):
        parser.add_argument('resume_id', type=str, help='Resume ID')

    def handle(self, *args, **options):
        resume_id = options['resume_id']
        try:
            resume = Resume.objects.get(id=resume_id)
            self.stdout.write(f"Processing resume: {resume.name}")
            
            # Read file
            file_path = resume.file_url.replace('/media/', '')
            file_content = default_storage.open(file_path).read()
            
            # Parse
            if resume.file_url.endswith('.pdf'):
                parsed_text = ResumeParser.parse_pdf(file_content)
            else:
                parsed_text = ResumeParser.parse_docx(file_content)
            
            # Update
            resume.parsed_text = parsed_text
            resume.status = 'completed'
            resume.save()
            
            self.stdout.write(self.style.SUCCESS(f"✅ Resume processed successfully!"))
            self.stdout.write(f"📄 Extracted {len(parsed_text)} characters")
            
        except Resume.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Resume {resume_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
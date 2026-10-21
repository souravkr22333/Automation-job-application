# backend/django_app/core/management/commands/cleanup_applications.py
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from applications.models import ApplicationQueue

class Command(BaseCommand):
    help = 'Clean up old application queue entries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        cutoff = now() - timedelta(days=days)
        
        # Delete old completed applications
        completed = ApplicationQueue.objects.filter(
            status=ApplicationQueue.Status.DONE,
            submitted_at__lt=cutoff
        )
        completed_count = completed.count()
        completed.delete()
        
        # Delete old failed applications
        failed = ApplicationQueue.objects.filter(
            status=ApplicationQueue.Status.FAILED,
            updated_at__lt=cutoff
        )
        failed_count = failed.count()
        failed.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up {completed_count} completed and {failed_count} failed applications'
            )
        )
# backend/django_app/core/management/commands/process_queue.py
from django.core.management.base import BaseCommand
from applications.tasks import process_queue_batch

class Command(BaseCommand):
    help = 'Process the auto-apply queue'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of items to process'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Processing queue...')
        result = process_queue_batch()
        self.stdout.write(
            self.style.SUCCESS(f'Processed {result.get("processed", 0)} items')
        )
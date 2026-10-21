# backend/django_app/config/celery.py
import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')

app = Celery('django_app')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery with better error handling
app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=5,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_max_memory_per_child=512 * 1024 * 1024,  # 512MB
    worker_concurrency=4,
    
    # Redis broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_retry_interval=5,
    broker_connection_retry_interval_start=1,
    broker_connection_retry_interval_step=2,
    broker_connection_retry_interval_max=30,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_compression='gzip',
    result_extended=True,
    
    # Beat schedule
    beat_schedule={
        'process-queue-batch': {
            'task': 'applications.tasks.process_queue_batch',
            'schedule': crontab(minute='*/5'),
        },
        'discover-jobs': {
            'task': 'jobs.tasks.discover_jobs_for_all_users',
            'schedule': crontab(hour='*/6'),
        },
        'cleanup-failed-applications': {
            'task': 'applications.tasks.cleanup_failed_applications',
            'schedule': crontab(hour=0, minute=0),
        },
    }
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
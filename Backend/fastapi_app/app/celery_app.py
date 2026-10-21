# backend/fastapi_app/celery_app.py
from celery import Celery
from .config import settings

celery_app = Celery(
    "auto_apply",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks",
        "app.services.resume_tailor",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_default_retry_delay=60,
    task_max_retries=5,
    task_soft_time_limit=600,
    task_time_limit=660,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_max_memory_per_child=512 * 1024 * 1024,  # 512MB
)

# Beat schedule
celery_app.conf.beat_schedule = {
    "process-queue-batch": {
        "task": "app.tasks.process_queue_batch",
        "schedule": 300.0,  # 5 minutes
    },
}
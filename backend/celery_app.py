"""
Celery Configuration for Async Task Processing
Handles document ingestion, cleanup jobs, and background tasks
"""

from celery import Celery
from core.config import settings

# Initialize Celery app
celery_app = Celery(
    "voice_knowledge_base",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.document_tasks",
        "tasks.cleanup_tasks",
        "tasks.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
    broker_connection_retry_on_startup=True,
)

# Scheduled tasks (beat schedule)
celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "tasks.cleanup_tasks.cleanup_expired_sessions",
        "schedule": 3600.0,  # Every hour
    },
    "cleanup-temp-files": {
        "task": "tasks.cleanup_tasks.cleanup_temp_files",
        "schedule": 86400.0,  # Daily
    },
    "sync-analytics": {
        "task": "tasks.notification_tasks.sync_analytics",
        "schedule": 300.0,  # Every 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
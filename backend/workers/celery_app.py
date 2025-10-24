"""
Celery application configuration for background tasks.
"""

from celery import Celery
from config import settings

# Create Celery app
celery_app = Celery(
    "nexus_analyzer",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)

# Configure Celery
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
    worker_max_tasks_per_child=1000,
    # Fix for Celery 6.0 deprecation warning
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(["workers"])

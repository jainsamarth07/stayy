"""Celery background tasks package — single shared Celery app instance."""

from celery import Celery

from app.config import settings

celery_app = Celery("staynest", broker=settings.CELERY_BROKER_URL)

# Task discovery
celery_app.conf.include = [
    "app.tasks.email_tasks",
    "app.tasks.membership_tasks",
]

# Reliability settings
celery_app.conf.update(
    task_acks_late=True,                   # Acknowledge after execution (requeue on crash)
    task_reject_on_worker_lost=True,       # Reject (requeue) if worker is killed
    task_time_limit=300,                   # Hard kill after 5 min
    task_soft_time_limit=240,              # SoftTimeLimitExceeded after 4 min
    worker_prefetch_multiplier=1,          # Fair scheduling
    result_expires=3600,                   # Discard results after 1 hr
)

# Celery Beat schedule — daily membership jobs
celery_app.conf.beat_schedule = {
    "check-expiring-memberships": {
        "task": "app.tasks.membership_tasks.check_expiring_memberships",
        "schedule": 86400.0,  # Every 24 hours
    },
    "process-auto-renewals": {
        "task": "app.tasks.membership_tasks.process_auto_renewals",
        "schedule": 86400.0,  # Every 24 hours
    },
}
celery_app.conf.timezone = "UTC"

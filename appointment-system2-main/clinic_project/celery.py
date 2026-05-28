# ============================================================
# clinic_project/celery.py
# Celery Configuration & Task Queue Setup
# ============================================================
"""
Celery configuration for the appointment system.
Handles asynchronous task scheduling and email notifications.
"""

import os
from celery import Celery
from celery.schedules import crontab
from decouple import config

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings')

# Create the Celery app
app = Celery('clinic_project')

# Load configuration from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# ============================================================
# CELERY CONFIGURATION
# ============================================================
app.conf.update(
    # ── Broker & Backend ──
    broker_url=config('CELERY_BROKER_URL', default='redis://localhost:6379/0'),
    result_backend=config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0'),
    
    # ── Task Configuration ──
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Manila',
    enable_utc=True,
    
    # ── Worker Configuration ──
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # ── Retry Configuration ──
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # ── Beat Schedule (Periodic Tasks) ──
    beat_schedule={
        # Check and send due appointment reminders every 5 minutes
        'send-appointment-reminders': {
            'task': 'appointments.tasks.send_due_appointment_reminders',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
            'options': {'queue': 'default'}
        },
        
        # Cleanup old scheduled tasks (optional, runs daily at 2 AM)
        'cleanup-expired-tasks': {
            'task': 'appointments.tasks.cleanup_expired_reminder_tasks',
            'schedule': crontab(hour=2, minute=0),
            'options': {'queue': 'default'}
        },
    },
)

# ============================================================
# TASK ERROR HANDLING & LOGGING
# ============================================================
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')


# ============================================================
# DEBUG: Print Celery Configuration on Startup
# ============================================================
if __name__ == '__main__':
    import logging
    logger = logging.getLogger('clinic_project.celery')
    logger.info("Celery app initialized successfully")
    logger.info(f"Broker: {app.conf.broker_url}")
    logger.info(f"Backend: {app.conf.result_backend}")

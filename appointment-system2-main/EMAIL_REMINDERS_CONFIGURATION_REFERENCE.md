# Configuration Reference — Timed Email Reminders

Quick reference for all configuration options and settings.

---

## Environment Variables (`.env`)

### Celery Configuration

```env
# Redis Message Broker (where tasks are queued)
CELERY_BROKER_URL=redis://localhost:6379/0

# Redis Result Backend (where task results are stored)
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Email Configuration

```env
# Email Backend
# - Console: prints to terminal (development)
# - SMTP: sends real emails (production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMTP Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Site URL (for email links)
SITE_URL=http://localhost:8000
```

---

## Django Settings (`clinic_project/settings.py`)

### Installed Apps

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'django_celery_beat',      # Periodic task scheduling
    'django_celery_results',   # Task result storage
    'appointments',            # Your app
]
```

### Celery Configuration

```python
# Broker and backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Task serialization (JSON for safety)
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'

# Timezone
CELERY_TIMEZONE = 'Asia/Manila'
CELERY_ENABLE_UTC = True

# Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_RESULT_EXTENDED = True
```

### Email Settings

```python
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@cliniccare.local')
SITE_URL = config('SITE_URL', default='http://localhost:8000')
```

---

## Appointment Model Configuration

### Database Fields

```python
class Appointment(models.Model):
    # ... existing fields ...
    
    # Reminder interval (in minutes)
    reminder_interval_minutes = models.PositiveIntegerField(default=30)
    
    # Track if reminder was sent
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Celery task ID for tracking/cancellation
    scheduled_task_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Track if "next in queue" notification was sent
    next_in_queue_notification_sent = models.BooleanField(default=False)
```

### Common Reminder Intervals

| Interval | Minutes | Use Case |
|----------|---------|----------|
| 15 minutes | 15 | Urgent/Quick appointments |
| 30 minutes | 30 | Standard (DEFAULT) |
| 1 hour | 60 | Flexible scheduling |
| 2 hours | 120 | All-day availability |
| 24 hours | 1440 | Important reminders |
| 48 hours | 2880 | Confirmation reminders |

---

## Celery Task Configuration

### Task Retries

```python
# In tasks.py - retry strategy for send_appointment_reminder()
send_appointment_reminder.apply_async(
    args=[appointment_id],
    countdown=seconds_until_reminder,
    retry=True,
    retry_policy={
        'max_retries': 3,          # Try up to 3 times
        'interval_start': 60,      # Start with 60 seconds
        'interval_step': 60,       # Add 60 seconds each retry
        'interval_max': 300,       # Max 5 minutes between retries
    }
)
```

### Beat Schedule (Periodic Tasks)

```python
# In celery.py
beat_schedule={
    'send-appointment-reminders': {
        'task': 'appointments.tasks.send_due_appointment_reminders',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'queue': 'default'}
    },
    'cleanup-expired-tasks': {
        'task': 'appointments.tasks.cleanup_expired_reminder_tasks',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'default'}
    },
}
```

---

## Email Template Variables

### Reminder Email (Online)

```html
<!-- Available variables in template -->
{{ patient_name }}              <!-- Patient's full name -->
{{ doctor_name }}               <!-- Doctor's full name -->
{{ appointment.date }}          <!-- Appointment date -->
{{ appointment.appointment_time }} <!-- Appointment time -->
{{ time_until_appointment }}    <!-- Time remaining (human readable) -->
{{ queue_number }}              <!-- Patient's queue number -->
{{ jitsi_link }}                <!-- Video call link -->
{{ appointment_details_url }}   <!-- Link to appointment details -->
{{ hospital_name }}             <!-- Clinic/Hospital name -->
```

### Reminder Email (In-Person)

```html
{{ patient_name }}
{{ doctor_name }}
{{ appointment.date }}
{{ appointment.appointment_time }}
{{ time_until_appointment }}
{{ queue_number }}
{{ hospital_name }}
{{ hospital_address }}
{{ appointment_details_url }}
```

### Next-in-Queue Email

```html
{{ patient_name }}
{{ doctor_name }}
{{ queue_number }}
{{ hospital_name }}
{{ hospital_address }}
{{ appointment_details_url }}
```

---

## Celery Command Reference

### Start Worker

```bash
# Standard mode
celery -A clinic_project worker -l info

# With concurrency limit
celery -A clinic_project worker -l info --concurrency=4

# Dedicated queue
celery -A clinic_project worker -Q reminders -l info
```

### Start Beat Scheduler

```bash
# Standard mode
celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# With persistent storage
celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler --pidfile=/tmp/celerybeat.pid
```

### Monitor with Flower

```bash
pip install flower
celery -A clinic_project flower
# Visit http://localhost:5555
```

### Check Task Queue

```bash
# View active tasks
celery -A clinic_project inspect active

# View scheduled tasks
celery -A clinic_project inspect scheduled

# Purge queue (WARNING: deletes all tasks!)
celery -A clinic_project purge
```

---

## Django Management Commands

### Test Email Reminders

```bash
# Create test appointments
python manage.py test_email_reminders --simulate

# With custom interval
python manage.py test_email_reminders --simulate --interval 120

# Send for specific appointment
python manage.py test_email_reminders --appointment-id 5

# Check pending reminders
python manage.py test_email_reminders --check-pending

# Test queue notification
python manage.py test_email_reminders --queue
```

---

## Database Queries

### Check Pending Reminders

```python
from appointments.models import Appointment
from django.utils import timezone

# Find appointments due for reminders
pending = Appointment.objects.filter(
    status__in=['confirmed', 'pending'],
    reminder_sent_at__isnull=True,
).order_by('date', 'appointment_time')

for appt in pending:
    reminder_time = appt.get_reminder_datetime()
    is_due = reminder_time <= timezone.now()
    print(f"Appt #{appt.id}: {reminder_time} - {'DUE' if is_due else 'PENDING'}")
```

### Check Scheduled Tasks

```python
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult

# View all periodic tasks
PeriodicTask.objects.all()

# View recent task results
TaskResult.objects.all().order_by('-date_created')[:10]
```

### Manual Task Execution

```python
from appointments.tasks import send_appointment_reminder
from appointments.models import Appointment

# Send reminder immediately
result = send_appointment_reminder(5)
print(result)

# Or queue it for later
task = send_appointment_reminder.apply_async(args=[5], countdown=3600)
print(f"Task ID: {task.id}")
```

---

## Production Deployment

### Email Providers

#### Gmail SMTP
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

#### SendGrid
```bash
pip install sendgrid-django
```

```env
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=your-key
```

#### AWS SES
```bash
pip install django-ses
```

```env
EMAIL_BACKEND=django_ses.SESBackend
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_SES_REGION_NAME=us-east-1
```

### Redis Providers

#### AWS ElastiCache
```env
CELERY_BROKER_URL=redis://your-redis-endpoint.ng.0001.use1.cache.amazonaws.com:6379/0
```

#### Heroku Redis
```env
CELERY_BROKER_URL=redis://h:password@host:port/0
```

#### Docker
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### Supervisor Configuration

**`/etc/supervisor/conf.d/celery.conf`:**
```ini
[program:celery_worker]
command=celery -A clinic_project worker -l info
directory=/path/to/clinic
user=www-data
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600

[program:celery_beat]
command=celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/clinic
user=www-data
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
```

---

## Monitoring & Logging

### Log Levels

```python
# In Django
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Celery Logging

```bash
# Info level (default)
celery -A clinic_project worker -l info

# Debug level (verbose)
celery -A clinic_project worker -l debug

# Warning level (quiet)
celery -A clinic_project worker -l warning
```

### Django Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/celery.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'appointments.tasks': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

## Performance Tuning

### Worker Settings

```bash
# Increase concurrency (processes)
celery -A clinic_project worker -l info --concurrency=16

# Set prefetch multiplier
celery -A clinic_project worker -l info --prefetch-multiplier=2

# Max tasks per child process
celery -A clinic_project worker -l info --max-tasks-per-child=1000
```

### Task Configuration

```python
# In tasks.py
@shared_task(
    bind=True,
    max_retries=3,
    time_limit=60,       # Hard limit: task killed after 60s
    soft_time_limit=50,  # Soft limit: task warned at 50s
    rate_limit='100/m',  # Rate limit: max 100 tasks/minute
)
def send_appointment_reminder(self, appointment_id):
    # ...
```

### Database Connection Pooling (Production)

```python
# In settings.py for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'CONN_MAX_AGE': 600,  # Connection pooling timeout
        'OPTIONS': {
            'isolation_level': pymysql.connections.ISOLATION_LEVELS['READ_COMMITTED'],
        }
    }
}
```

---

## Troubleshooting Checklist

| Issue | Check | Fix |
|-------|-------|-----|
| Emails not sending | EMAIL_BACKEND | Verify in settings.py |
| Worker not running | `celery -A clinic_project worker -l info` | Restart worker |
| Tasks not executing | Celery Beat running? | Start beat process |
| Redis connection error | `redis-cli ping` | Start/restart Redis |
| Wrong reminder time | Timezone setting | Check CELERY_TIMEZONE |
| Duplicate reminders | Check reminder_sent_at | Database migration ran? |
| Slow email sending | Rate limiting | Adjust rate_limit in task |

---

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django-Celery-Beat](https://github.com/celery/django-celery-beat)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring](https://flower.readthedocs.io/)

---

**For detailed setup instructions, see [EMAIL_REMINDERS_QUICK_START.md](EMAIL_REMINDERS_QUICK_START.md)**

**For comprehensive documentation, see [EMAIL_REMINDERS_IMPLEMENTATION.md](EMAIL_REMINDERS_IMPLEMENTATION.md)**

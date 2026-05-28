# Timed Email Notifications for Patient Queues — Implementation Guide

## Overview

This system implements **timed, asynchronous email notifications** for patient appointments using Celery, Redis, and Django signals. It sends:

1. **Immediate confirmation emails** when a patient books an appointment
2. **Scheduled reminder emails** at configurable intervals (30 minutes, 2 hours, 24 hours, etc.) before the appointment
3. **"Next in queue" notifications** when a patient is about to be seen by the doctor

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PATIENT BOOKS APPOINTMENT                                      │
└─────────────────────────────────────────────────────────────────┘
              ↓
    ┌─────────────────────┐
    │ Signal: Appointment │
    │ Status → Confirmed  │
    └─────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ 1. Send Confirmation Email (Immediately)            │
    │ 2. Calculate Reminder Time = Appointment - Interval │
    │ 3. Schedule Celery Task with apply_async()          │
    │ 4. Store Task ID & Reminder Time in Database        │
    └──────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ Celery Beat (Every 5 minutes)                       │
    │ → Check for appointments due for reminders          │
    │ → Execute send_due_appointment_reminders task       │
    └──────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ REMINDER EMAIL SENT AT EXACT TIME                   │
    │ (e.g., 30 minutes before appointment)               │
    └──────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ APPOINTMENT TIME REACHED                            │
    │ Doctor marks appointment as "in_progress"           │
    └──────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ Signal: Status → In Progress                        │
    │ → Schedule "Next in Queue" Email for Next Patient   │
    └──────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────────────────────────────────────┐
    │ NEXT PATIENT RECEIVES "YOU'RE NEXT" EMAIL           │
    │ Patient proceeds to clinic immediately             │
    └──────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. **Appointment Model** ([models.py](appointments/models.py))

New fields added:

```python
class Appointment(models.Model):
    # ... existing fields ...
    
    # Reminder scheduling
    reminder_interval_minutes = models.PositiveIntegerField(default=30)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    scheduled_task_id = models.CharField(max_length=255, blank=True, null=True)
    next_in_queue_notification_sent = models.BooleanField(default=False)
    
    # Methods
    def get_appointment_datetime(self):
        """Returns timezone-aware datetime combining date + appointment_time"""
    
    def get_reminder_datetime(self):
        """Returns when reminder should be sent (appointment_datetime - interval)"""
```

### 2. **Celery Configuration** ([clinic_project/celery.py](clinic_project/celery.py))

- **Broker**: Redis (message queue)
- **Backend**: Redis (result storage)
- **Beat Schedule**: Checks for due reminders every 5 minutes
- **Serializer**: JSON (safe, language-agnostic)

### 3. **Celery Tasks** ([appointments/tasks.py](appointments/tasks.py))

#### Main Tasks:

| Task | Purpose | Trigger |
|------|---------|---------|
| `send_appointment_reminder()` | Sends reminder email for specific appointment | Celery Beat or apply_async() |
| `send_due_appointment_reminders()` | Periodic task checking all due reminders | Celery Beat (every 5 min) |
| `send_next_in_queue_notification()` | Sends "you're next" email | Signal when status → in_progress |
| `cleanup_expired_reminder_tasks()` | Clears task IDs for completed appointments | Celery Beat (daily at 2 AM) |

#### Helper Functions:

```python
_send_reminder_email_to_patient(appointment)
_send_next_in_queue_email(appointment)
```

### 4. **Signals** ([appointments/signals.py](appointments/signals.py))

```python
@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    """Triggers when appointment is created or status changes"""
    
    if instance.status == 'confirmed':
        # 1. Send confirmation email
        # 2. Calculate reminder time
        # 3. Schedule Celery task with apply_async(countdown=...)
        # 4. Store task ID
    
    elif instance.status == 'cancelled':
        # Revoke scheduled Celery task
    
    elif instance.status == 'in_progress':
        # Schedule "next in queue" notification
```

### 5. **Email Templates**

Three new HTML email templates:

- `templates/emails/appointment_reminder_online.html` — Online consultation reminder
- `templates/emails/appointment_reminder_inperson.html` — In-person appointment reminder
- `templates/emails/next_in_queue_notification.html` — "You're next!" notification

---

## Installation & Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `celery>=5.3.0` — Task queue
- `redis>=5.0.0` — Message broker & result backend
- `django-celery-beat>=2.5.0` — Periodic task scheduler
- `django-celery-results>=2.5.0` — Stores task results in database

### Step 2: Start Redis Server

**On Mac/Linux:**
```bash
# Using Homebrew
brew services start redis

# Or manually
redis-server
```

**On Windows:**
```bash
# Using Windows Subsystem for Linux or Docker
docker run -d -p 6379:6379 redis:latest

# Or download Redis for Windows from:
# https://github.com/microsoftarchive/redis/releases
```

**Verify Redis is running:**
```bash
redis-cli ping
# Expected output: PONG
```

### Step 3: Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the necessary database tables for django-celery-beat and new Appointment fields.

### Step 4: Configure Django Settings

See [clinic_project/settings.py](clinic_project/settings.py) for Celery and Email configuration.

### Step 5: Start Celery Worker & Beat

**Terminal 1 — Celery Worker** (processes tasks):
```bash
celery -A clinic_project worker -l info
```

**Terminal 2 — Celery Beat** (schedules periodic tasks):
```bash
celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Terminal 3 — Django Development Server** (existing):
```bash
python manage.py runserver
```

---

## Email Configuration

### Development: Console Backend (No External Email)

By default, emails print to the console (in Terminal 3).

**In settings.py:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Production: Gmail SMTP

**1. Enable 2-Step Verification on Gmail account**
- Go to https://myaccount.google.com/security

**2. Generate App Password**
- Go to https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer" (or your device)
- Copy the generated 16-character password

**3. Update `.env` file:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**4. Restart Django server**

---

## How It Works: Step-by-Step

### Scenario: Patient Books Appointment

**Time: 2:00 PM — Patient books appointment for 4:00 PM**

```
1. Patient submits appointment form
   ↓
2. Appointment created with status='pending'
   Signal fires → appointment_notification()
   ↓
3. Admin/Doctor confirms appointment → status='confirmed'
   Signal fires again → appointment_notification()
   ↓
4. Signal calculates reminder time:
   reminder_time = 4:00 PM - 30 minutes = 3:30 PM
   ↓
5. Celery task scheduled with apply_async(countdown=90 minutes)
   scheduled_task_id stored in database
   ↓
6. Send confirmation email immediately
   ↓
7. [WAITING...]
   ↓
   3:30 PM — Celery Beat detects task is due
   ↓
8. send_appointment_reminder task executes
   ↓
9. Reminder email sent to patient
   reminder_sent_at = 3:30 PM
   ↓
10. [WAITING...]
    ↓
    4:00 PM — Appointment time arrives
    ↓
11. Doctor marks appointment as 'in_progress'
    ↓
12. Signal detects status change → finds next patient in queue
    ↓
13. Schedule send_next_in_queue_notification task
    ↓
14. "You're next in queue!" email sent to next patient
```

---

## Customizing Reminder Intervals

### Global Default

Edit [settings.py](clinic_project/settings.py) or [models.py](appointments/models.py):

```python
# In Appointment model
reminder_interval_minutes = models.PositiveIntegerField(default=30)
```

### Per-Appointment

When creating/updating appointments programmatically:

```python
# 24-hour reminder
appointment.reminder_interval_minutes = 24 * 60  # 1440 minutes

# 2-hour reminder
appointment.reminder_interval_minutes = 2 * 60   # 120 minutes

# 15-minute reminder
appointment.reminder_interval_minutes = 15

appointment.save()
```

### Via Admin

When confirming appointments in admin panel:
1. Edit appointment
2. Adjust `reminder_interval_minutes` field
3. Save (will reschedule task)

---

## Testing the System

### Command 1: Create Test Appointments

```bash
python manage.py test_email_reminders --simulate
```

Creates test appointments with 30-minute reminders. Watch console for emails.

### Command 2: Test with Custom Interval

```bash
python manage.py test_email_reminders --simulate --interval 1
```

Creates appointment with 1-minute reminder (for quick testing).

### Command 3: Test Specific Appointment

```bash
python manage.py test_email_reminders --appointment-id 5
```

Sends reminder for appointment #5 immediately.

### Command 4: Check Pending Reminders

```bash
python manage.py test_email_reminders --check-pending
```

Shows all appointments waiting to send reminders.

### Command 5: Test Queue Notification

```bash
python manage.py test_email_reminders --queue
```

Tests "next in queue" notification system.

---

## Monitoring & Debugging

### View Celery Tasks

**Check all scheduled tasks:**
```bash
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

**Check task results:**
```python
>>> from django_celery_results.models import TaskResult
>>> TaskResult.objects.all()[:10]
```

### Monitor Logs

Django logs are in console output:

```
[2:30 PM] Scheduled reminder task abc123def456 for appointment 5 at 2024-05-28 14:30:00+0800 (in 3600 seconds)
[3:30 PM] Reminder email sent for appointment 5 (patient: patient@example.com)
[4:00 PM] Scheduled next-in-queue notification task xyz789 for appointment 6
```

### Check Redis Connection

```bash
redis-cli info stats
redis-cli KEYS "celery*"  # View Celery keys in Redis
```

### Django Shell Testing

```bash
python manage.py shell

# Test reminder time calculation
>>> from appointments.models import Appointment
>>> appt = Appointment.objects.get(id=5)
>>> appt.get_appointment_datetime()
datetime.datetime(2024, 5, 28, 16, 0, tzinfo=<DstTzInfo 'Asia/Manila' PHT+8:00, PHA+8:00>)
>>> appt.get_reminder_datetime()
datetime.datetime(2024, 5, 28, 15, 30, tzinfo=<DstTzInfo 'Asia/Manila' PHT+8:00, PHA+8:00>)

# Manual task execution
>>> from appointments.tasks import send_appointment_reminder
>>> result = send_appointment_reminder(5)
>>> print(result)
{'status': 'sent', 'appointment_id': 5, 'patient_email': 'patient@example.com', ...}
```

---

## Troubleshooting

### Issue: Emails not sending

**Check:**
1. ✅ Is Celery worker running? (`celery -A clinic_project worker -l info`)
2. ✅ Is Celery Beat running? (`celery -A clinic_project beat -l info`)
3. ✅ Is Redis running? (`redis-cli ping` → should return `PONG`)
4. ✅ Check Django logs for errors
5. ✅ Verify EMAIL_BACKEND in settings.py

### Issue: Reminder email sent at wrong time

**Check:**
1. ✅ Is timezone correct? (Should be `Asia/Manila`)
2. ✅ Is `reminder_interval_minutes` correct?
3. ✅ Use shell to verify: `appt.get_reminder_datetime()`

### Issue: Celery worker not picking up tasks

**Fix:**
```bash
# Restart worker
celery -A clinic_project worker -l info

# Check if tasks exist
redis-cli KEYS "*celery*"
```

### Issue: Database errors after migration

**Fix:**
```bash
# Clear and re-apply migrations
python manage.py migrate appointments zero
python manage.py migrate appointments
python manage.py migrate django_celery_beat
```

---

## Production Deployment

### 1. Use Supervisor for Process Management

**Create `/etc/supervisor/conf.d/celery.conf`:**
```ini
[program:celery_worker]
command=celery -A clinic_project worker -l info
directory=/path/to/clinic
user=www-data
autostart=true
autorestart=true

[program:celery_beat]
command=celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/clinic
user=www-data
autostart=true
autorestart=true
```

### 2. Use External Redis (e.g., AWS ElastiCache)

Update `.env`:
```env
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0
```

### 3. Enable Transactional Email Service (Optional)

```env
# SendGrid
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=your-sendgrid-key

# Or AWS SES
EMAIL_BACKEND=django_ses.SESBackend
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_SES_REGION_NAME=us-east-1
```

### 4. Set Up Logging

**In settings.py:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/celery.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
        },
    },
    'loggers': {
        'appointments.tasks': {
            'handlers': ['celery_file'],
            'level': 'INFO',
        },
    },
}
```

### 5. Set Up Monitoring (Optional)

- **Flower**: Celery monitoring UI
  ```bash
  pip install flower
  celery -A clinic_project flower
  # Visit http://localhost:5555
  ```

---

## API Reference

### Celery Tasks

#### `send_appointment_reminder(appointment_id)`

**Purpose:** Send reminder email for specific appointment

**Parameters:**
- `appointment_id` (int): ID of appointment

**Returns:**
```python
{
    'status': 'sent',
    'appointment_id': 5,
    'patient_email': 'patient@example.com',
    'reminder_time': '2024-05-28T14:30:00+08:00',
    'appointment_time': '2024-05-28T15:00:00+08:00',
}
```

**Example:**
```python
from appointments.tasks import send_appointment_reminder

# Schedule for later
task = send_appointment_reminder.apply_async(args=[5], countdown=3600)
print(task.id)  # Get task ID for tracking

# Execute immediately
result = send_appointment_reminder(5)
```

#### `send_due_appointment_reminders()`

**Purpose:** Periodic task to find and send all due reminders

**Returns:**
```python
{
    'task': 'send_due_appointment_reminders',
    'timestamp': '2024-05-28T14:30:00+08:00',
    'sent': 3,
    'errors': 0,
    'skipped': 5,
}
```

#### `send_next_in_queue_notification(appointment_id)`

**Purpose:** Send "you're next in queue" email

**Parameters:**
- `appointment_id` (int): ID of next appointment

**Returns:**
```python
{
    'status': 'sent',
    'appointment_id': 6,
    'patient_email': 'next.patient@example.com',
    'queue_number': 2,
}
```

### Appointment Model Methods

#### `get_appointment_datetime()`

**Returns:** Timezone-aware datetime of appointment

```python
appt = Appointment.objects.get(id=5)
dt = appt.get_appointment_datetime()
# → datetime(2024, 5, 28, 15, 0, tzinfo=<Manila>)
```

#### `get_reminder_datetime()`

**Returns:** When reminder should be sent

```python
reminder_dt = appt.get_reminder_datetime()
# → datetime(2024, 5, 28, 14, 30, tzinfo=<Manila>)
# (15:00 - 30 minutes)
```

---

## Files Modified/Created

### New Files
- ✅ [clinic_project/celery.py](clinic_project/celery.py) — Celery configuration
- ✅ [appointments/tasks.py](appointments/tasks.py) — Celery tasks
- ✅ [appointments/migrations/0019_email_reminders_task_scheduling.py](appointments/migrations/0019_email_reminders_task_scheduling.py) — Database migration
- ✅ [appointments/management/commands/test_email_reminders.py](appointments/management/commands/test_email_reminders.py) — Testing command
- ✅ `templates/emails/appointment_reminder_online.html` — Online reminder template
- ✅ `templates/emails/appointment_reminder_inperson.html` — In-person reminder template
- ✅ `templates/emails/next_in_queue_notification.html` — Queue notification template

### Modified Files
- ✅ [requirements.txt](requirements.txt) — Added Celery, Redis, Django Celery packages
- ✅ [clinic_project/__init__.py](clinic_project/__init__.py) — Import Celery app
- ✅ [clinic_project/settings.py](clinic_project/settings.py) — Celery and email configuration
- ✅ [appointments/models.py](appointments/models.py) — New reminder fields and methods
- ✅ [appointments/signals.py](appointments/signals.py) — Schedule Celery tasks
- ✅ [appointments/email_utils.py](appointments/email_utils.py) — (No changes; kept as-is)

---

## Summary

| Feature | Implementation |
|---------|-----------------|
| **Immediate Confirmation** | Django signal sends email when status='confirmed' |
| **Timed Reminders** | Celery apply_async() with countdown parameter |
| **Periodic Check** | Celery Beat runs every 5 minutes |
| **Queue Notifications** | Signal triggers when status='in_progress' |
| **Customizable Intervals** | Stored per-appointment in database |
| **Task Tracking** | Task ID stored for monitoring/cancellation |
| **Email Backend** | Console (dev), Gmail SMTP (prod) |
| **Message Broker** | Redis |
| **Result Backend** | Redis |
| **Timezone Support** | Asia/Manila configured in settings |

---

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start Redis**: `redis-server`
3. **Migrate database**: `python manage.py migrate`
4. **Start Celery Worker**: `celery -A clinic_project worker -l info`
5. **Start Celery Beat**: `celery -A clinic_project beat -l info`
6. **Test system**: `python manage.py test_email_reminders --simulate`
7. **Monitor**: Check console for emails and logs

---

**For questions or issues, check the Troubleshooting section or review the code comments in the implementation files.**

# Email Reminders — Quick Start Guide

Get the appointment reminder system up and running in 10 minutes.

---

## Prerequisites

- Python 3.9+
- Redis installed and running
- Django project already configured

---

## 1. Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

---

## 2. Configure Environment (2 min)

**Copy `.env.example` to `.env`:**
```bash
cp .env.example .env
```

**Update `.env` with Redis URL (optional if running locally):**
```env
# Default (already set in .env.example)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 3. Start Redis (1 min)

**Option A: Using Homebrew (Mac)**
```bash
brew services start redis
# Verify: redis-cli ping → PONG
```

**Option B: Using Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option C: Using Windows**
```bash
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use WSL (Windows Subsystem for Linux)
```

---

## 4. Apply Database Migration (1 min)

```bash
python manage.py migrate
```

This creates tables for:
- Celery Beat periodic tasks
- Celery results
- New appointment reminder fields

---

## 5. Start Celery Services (4 min)

**Open 3 separate terminals:**

**Terminal 1 — Celery Worker** (processes tasks):
```bash
celery -A clinic_project worker -l info
```

**Terminal 2 — Celery Beat** (schedules periodic tasks):
```bash
celery -A clinic_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Terminal 3 — Django Development Server** (if not already running):
```bash
python manage.py runserver
```

**Expected output in Terminal 1:**
```
 -------------- celery@hostname v5.3.0 (emerald-rush)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ---------- .celery(): celery
- ** ---------- .broker(): redis://localhost:6379/0
- ** ---------- .loader(): celery.loaders.app.AppLoader
- ** ---------- .pidfile(): /var/run/celery.pid
- ** ---------- .uid(): 501
- ** ---------- .gid(): 20
- ** ---------- .loglevel(): INFO
- ** ---------- .concurrency(): 8
- *** --- * --- .prefetch_multiplier(): 4
-- ******* ---- .accept_content(): ['json']
--- ***** ----- .hostname(): celery@MacBook.local
 -------------- [queues]
                .celery: exchange:celery type:direct key:celery
```

---

## 6. Test the System (1 min)

**Create test appointments with 1-minute reminders:**
```bash
python manage.py test_email_reminders --simulate --interval 1
```

**Watch the output:**
1. You'll see "✓ Created test appointment"
2. Check Terminal 3 (Django) for confirmation email
3. In 1 minute, check Terminal 1 (Worker) for reminder email

**You should see:**
```
[2:30 PM] Online appointment confirmation email sent for appointment 5
[2:31 PM] Reminder email sent for appointment 5 (patient: patient@test.local)
```

---

## 7. Check Other Commands

**View pending reminders:**
```bash
python manage.py test_email_reminders --check-pending
```

**Test specific appointment:**
```bash
python manage.py test_email_reminders --appointment-id 5
```

**Get help:**
```bash
python manage.py test_email_reminders --help
```

---

## Production Checklist

- [ ] Update `.env` with production Redis URL
- [ ] Configure Gmail SMTP (EMAIL_BACKEND, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
- [ ] Use Supervisor for process management
- [ ] Set up Flower monitoring (`pip install flower`)
- [ ] Configure logging to file
- [ ] Test with production email domain

---

## Common Issues

### ❌ "Connection refused" for Redis
- Verify Redis is running: `redis-cli ping` → should return `PONG`
- Check Redis URL in .env

### ❌ "Celery worker not picking up tasks"
- Verify worker is running in Terminal 1
- Check for errors in worker output
- Restart: `Ctrl+C` then run command again

### ❌ "No emails in console"
- Check if Django development server is running (Terminal 3)
- Verify EMAIL_BACKEND is set correctly in .env

### ❌ "Task stuck/not executing"
- Verify Celery Beat is running (Terminal 2)
- Check logs for errors
- Restart both worker and beat services

---

## What Happens Next

1. **Patient books appointment** → Confirmation email sent immediately
2. **Admin confirms appointment** → Reminder task scheduled for 30 minutes before
3. **Celery Beat wakes up every 5 minutes** → Checks for due reminders
4. **At reminder time** → Reminder email automatically sent
5. **Appointment time reached** → Doctor marks as "in progress"
6. **Next patient notified** → "You're next!" email sent

---

## Customize Reminder Time

**Global default** (in [appointments/models.py](appointments/models.py)):
```python
reminder_interval_minutes = models.PositiveIntegerField(default=30)
```

**Per-appointment** (in admin or code):
```python
appointment.reminder_interval_minutes = 60  # 1 hour before
appointment.save()
```

---

## Monitor System

**Real-time monitoring UI (optional):**
```bash
pip install flower
celery -A clinic_project flower
# Visit http://localhost:5555
```

---

## Full Documentation

For detailed setup, configuration, troubleshooting, and production deployment:

→ See [EMAIL_REMINDERS_IMPLEMENTATION.md](EMAIL_REMINDERS_IMPLEMENTATION.md)

---

**Ready? Start with Step 1! You'll have working reminders in ~10 minutes. 🚀**

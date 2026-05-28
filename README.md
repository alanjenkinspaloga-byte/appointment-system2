# ============================================================
# CLINIC APPOINTMENT SYSTEM — Setup Guide
# ============================================================
# Django + MySQL (XAMPP) Web Application
# ============================================================


## PROJECT STRUCTURE

```
Appointment System/
│
├── manage.py                          # Django management script
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
│
├── clinic_project/                    # Django project config
│   ├── __init__.py
│   ├── settings.py                    # Project settings (MySQL config here)
│   ├── urls.py                        # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── appointments/                      # Main Django app
│   ├── __init__.py
│   ├── apps.py                        # App configuration
│   ├── models.py                      # Database models (6 models)
│   ├── views.py                       # All views (class-based)
│   ├── forms.py                       # Django ModelForms
│   ├── urls.py                        # App URL routing
│   ├── admin.py                       # Admin panel registration
│   ├── decorators.py                  # Role-based access decorators
│   ├── signals.py                     # Auto-create profile on user creation
│   └── tests.py                       # Tests (placeholder)
│
├── templates/                         # HTML templates
│   ├── base.html                      # Master template (Bootstrap 5)
│   ├── home.html                      # Landing page
│   │
│   ├── registration/
│   │   ├── register.html              # Registration form
│   │   └── login.html                 # Login form
│   │
│   ├── profile/
│   │   └── profile.html               # Edit profile
│   │
│   ├── doctor/
│   │   ├── sidebar.html               # Doctor sidebar navigation
│   │   ├── dashboard.html             # Doctor dashboard
│   │   ├── availability_list.html     # View all availability slots
│   │   ├── availability_form.html     # Add/edit availability
│   │   ├── appointment_list.html      # All appointments with filters
│   │   ├── appointment_detail.html    # View & update appointment status
│   │   ├── history.html               # Past/completed appointments
│   │   ├── today_patients.html        # Today's patient queue
│   │   └── record_payment.html        # Record payment for appointment
│   │
│   └── patient/
│       ├── sidebar.html               # Patient sidebar navigation
│       ├── dashboard.html             # Patient dashboard
│       ├── doctor_list.html           # Browse available doctors
│       ├── doctor_schedule.html       # View doctor's schedule
│       ├── book_appointment.html      # Book appointment form
│       ├── appointment_list.html      # My appointments list
│       └── appointment_detail.html    # Appointment detail + queue + payment
│
└── static/
    ├── css/
    │   └── style.css                  # Custom styles
    └── js/
        └── script.js                  # Custom JavaScript
```


## STEP-BY-STEP SETUP GUIDE

### Prerequisites
- Python 3.10+ installed
- XAMPP installed (for MySQL)
- pip (Python package manager)

---

### Step 1: Start XAMPP MySQL

1. Open **XAMPP Control Panel**
2. Click **Start** next to **Apache**
3. Click **Start** next to **MySQL**
4. Open browser → go to **http://localhost/phpmyadmin**
5. Click **"New"** on the left sidebar
6. Enter database name: **clinic_db**
7. Set collation to: **utf8mb4_general_ci**
8. Click **Create**

---

### Step 2: Create Virtual Environment

Open a terminal in the project folder and run:

```bash
# Navigate to project directory
cd "C:\Users\Bry\Desktop\Appointment System"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate
```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **Django** — The web framework
- **mysqlclient** — MySQL database connector for Django

> **Note:** If `mysqlclient` fails to install, try:
> ```bash
> pip install pymysql
> ```
> Then add this to `clinic_project/__init__.py`:
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

---

### Step 4: Verify Database Settings

Open `clinic_project/settings.py` and check the DATABASES section:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'clinic_db',
        'USER': 'root',
        'PASSWORD': '',           # Default XAMPP has no password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

### Step 5: Run Migrations

```bash
# Create migration files from models
python manage.py makemigrations

# Apply migrations to create database tables
python manage.py migrate
```

---

### Step 6: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Enter a username, email, and password when prompted.

---

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

Open browser → **http://127.0.0.1:8000/**

---

### Step 8: Access the System

| URL                                  | Description                    |
|--------------------------------------|--------------------------------|
| http://127.0.0.1:8000/              | Home / Landing page            |
| http://127.0.0.1:8000/register/     | Register as Doctor or Patient  |
| http://127.0.0.1:8000/login/        | Login                          |
| http://127.0.0.1:8000/dashboard/    | Dashboard (redirects by role)  |
| http://127.0.0.1:8000/admin/        | Django Admin Panel             |


## DATABASE MODELS

| Model         | Purpose                                      |
|---------------|----------------------------------------------|
| Profile       | Extends User with role (Doctor/Patient)       |
| Doctor        | Doctor info (specialization, fee, license)    |
| Patient       | Patient info (DOB, gender, emergency contact) |
| Availability  | Doctor schedule slots (date, time, location)  |
| Appointment   | Booking record with status and queue number   |
| Payment       | Payment info linked to appointment            |


## KEY FEATURES

### Doctor Features
- Dashboard with today's stats
- Create/edit/delete availability schedule
- View & filter all appointments
- Approve/reject appointment requests
- Update appointment status (Pending → Approved → In Progress → Completed)
- Auto-generated queue numbers per doctor per day
- View today's patient queue
- Record payments
- View appointment history

### Patient Features
- Dashboard with upcoming appointments
- Browse available doctors
- View doctor schedules
- Book appointments on available slots
- View booking status
- See queue number after approval
- View payment status

### System Logic
- Prevents double-booking (same slot can't be booked twice)
- Prevents same patient from booking same slot
- Auto-generates queue numbers when appointment is approved
- Queue numbers reset per doctor per day
- Role-based access control (decorators)
- Django messages for user feedback


## URL ROUTES

### Authentication
- `/` — Home page
- `/register/` — Register
- `/login/` — Login
- `/logout/` — Logout
- `/profile/` — Edit profile

### Doctor
- `/doctor/dashboard/` — Dashboard
- `/doctor/availability/` — List availability
- `/doctor/availability/add/` — Add availability slot
- `/doctor/availability/<id>/edit/` — Edit slot
- `/doctor/availability/<id>/delete/` — Delete slot
- `/doctor/appointments/` — All appointments
- `/doctor/appointments/<id>/` — Appointment detail + update
- `/doctor/today-patients/` — Today's queue
- `/doctor/history/` — Past records
- `/doctor/payment/<id>/` — Record payment

### Patient
- `/patient/dashboard/` — Dashboard
- `/patient/doctors/` — Doctor list
- `/patient/doctors/<id>/schedule/` — Doctor schedule
- `/patient/book/<id>/` — Book appointment
- `/patient/appointments/` — My appointments
- `/patient/appointments/<id>/` — Appointment detail


## TROUBLESHOOTING

### "No module named 'MySQLdb'"
Install `mysqlclient` or use `pymysql` as described in Step 3.

### "Access denied for user 'root'@'localhost'"
Check that XAMPP MySQL is running and the password in `settings.py` matches.

### "Database 'clinic_db' doesn't exist"
Create it in phpMyAdmin (Step 1).

### Static files not loading
Run: `python manage.py collectstatic`

---

**Built with Django, Bootstrap 5, and MySQL (XAMPP)**

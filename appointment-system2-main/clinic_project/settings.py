# ============================================================
# Clinic Appointment System — Django Project Settings
# ============================================================
# This file configures the Django project. Key sections:
#   • Database (MySQL via XAMPP)
#   • Installed apps
#   • Authentication redirects
#   • Static / media files
# ============================================================

import os
from pathlib import Path
from decouple import config

# --------------------------------------------------
# BASE DIRECTORY
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# SECURITY — Load from environment variables
# --------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production-abc123xyz')

DEBUG = config('DEBUG', default=True, cast=bool)

# Parse ALLOWED_HOSTS from environment, with fallback that includes Render domain
_allowed_hosts_env = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,appointment-system2.onrender.com,digitalonlineclinicscheduling.site')
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts_env.split(',')]

# --------------------------------------------------
# INSTALLED APPS
# --------------------------------------------------
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required by django-allauth

    # Celery task scheduling
    'django_celery_beat',
    'django_celery_results',

    # Django-allauth (Google OAuth & Social Authentication)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Our custom app
    'appointments',
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================
# AUTHENTICATION & DJANGO-ALLAUTH CONFIGURATION
# ============================================================
# Authentication backends for Django-Allauth (Google OAuth)
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Site ID for django.contrib.sites (required by allauth)
SITE_ID = 1

# ============================================================
# DJANGO-ALLAUTH CONFIGURATION
# ============================================================
# Email verification (optional=allow signup without email confirmation)
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Allow authentication with email or username
ACCOUNT_AUTHENTICATION_METHOD = 'email'

# Require email on signup
ACCOUNT_EMAIL_REQUIRED = True

# Unique email requirement
ACCOUNT_UNIQUE_EMAIL = True

# Social account auto-signup
SOCIALACCOUNT_AUTO_SIGNUP = True

# Auto-connect social accounts on login if email matches
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'

# Store OAuth tokens in database for API access later
SOCIALACCOUNT_STORE_TOKENS = True

# Adapter for Google OAuth
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# Google OAuth provider settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_OAUTH_CLIENT_ID', default=''),
            'secret': config('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
            'key': ''  # Not used for Google
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# --------------------------------------------------
# URL CONFIGURATION
# --------------------------------------------------
ROOT_URLCONF = 'clinic_project.urls'

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'appointments.context_processors.notifications',
                'appointments.context_processors.google_calendar_context',
            ],
        },
    },
]

# --------------------------------------------------
# WSGI
# --------------------------------------------------
WSGI_APPLICATION = 'clinic_project.wsgi.application'

# ============================================================
# DATABASE — MySQL (Local or Remote)
# ============================================================
# Load database credentials from environment variables
# Defaults to local XAMPP for development
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DB_NAME', default='clinic_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='Jenkins_13'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# --------------------------------------------------
# PASSWORD VALIDATORS
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # Philippine timezone
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# STATIC FILES (CSS, JavaScript, images)
# --------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --------------------------------------------------
# MEDIA FILES (user uploads)
# --------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# AUTHENTICATION REDIRECTS
# --------------------------------------------------
LOGIN_URL = '/login/'              # Where to redirect if not logged in
LOGIN_REDIRECT_URL = '/dashboard/' # Where to go after successful login
LOGOUT_REDIRECT_URL = '/login/'    # Where to go after logout

# ============================================================
# GOOGLE CALENDAR API CONFIGURATION
# ============================================================
GOOGLE_OAUTH_CREDENTIALS_FILE = config(
    'GOOGLE_OAUTH_CREDENTIALS_FILE',
    default=str(BASE_DIR / 'google_oauth_credentials.json')
)

GOOGLE_CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
]

# Google Meet conference settings
GOOGLE_MEET_CONFIG = {
    'enabled': True,
    'conference_solution': 'hangoutsMeet',
    'duration_minutes': 30,
    'time_zone': TIME_ZONE,
}


# --------------------------------------------------
# EMAIL — console backend for development
# (Change to SMTP in production)
# --------------------------------------------------
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

# Gmail SMTP Configuration (populate in .env for production)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@cliniccare.local')

# Site URL for email templates (used in generating full URLs for emails)
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# --------------------------------------------------
# MESSAGES FRAMEWORK — Bootstrap CSS classes
# --------------------------------------------------
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# ============================================================
# CELERY — TASK QUEUE & SCHEDULER CONFIGURATION
# ============================================================
# Celery broker: Redis (message queue for task coordination)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')

# Celery result backend: Redis (stores task results)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Celery task configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Manila'
CELERY_ENABLE_UTC = True

# Django-Celery-Beat: persistent storage for periodic tasks
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_RESULT_EXTENDED = True

# ============================================================
# GOOGLE OAUTH SOCIAL AUTHENTICATION (django-allauth)
# ============================================================
# Securely store Google OAuth credentials in environment variables
# Obtain credentials from: https://console.cloud.google.com/

# Redirect URI (must match Google Cloud Console)
# Development: http://localhost:8000/accounts/google/login/callback/
# Production: https://yourdomain.com/accounts/google/login/callback/
GOOGLE_OAUTH_CALLBACK_URL = config(
    'GOOGLE_OAUTH_CALLBACK_URL',
    default='http://localhost:8000/accounts/google/login/callback/'
)

# Google OAuth Sign-In Setup Guide

Complete guide to integrate Google OAuth patient sign-in into your Django appointment system using django-allauth.

---

## Overview

This integration allows patients to sign in using their Google accounts. The process:

1. Patient clicks "Sign in with Google" button
2. Redirected to Google login page
3. After authentication, redirected back to your app
4. User automatically created/authenticated in Django
5. Redirected to dashboard with session active

---

## Part 1: Google Cloud Console Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "NEW PROJECT"
4. Name: "OkiDoki Clinic" (or your app name)
5. Click "CREATE"
6. Wait for project creation (1-2 minutes)

### Step 2: Enable Google+ API

1. In Cloud Console, search for "Google+ API"
2. Click on "Google+ API" result
3. Click "ENABLE"
4. Wait for activation

### Step 3: Create OAuth 2.0 Credentials

1. In left sidebar, click "Credentials"
2. Click "CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, click "Configure Consent Screen" first
4. On Consent Screen:
   - User Type: **External**
   - Click "CREATE"
   - Fill required fields:
     - App name: "OkiDoki Clinic"
     - User support email: your-email@gmail.com
     - Developer contact: your-email@gmail.com
   - Click "SAVE AND CONTINUE"
   - Click through remaining sections
   - Click "BACK TO DASHBOARD"

### Step 4: Create OAuth Credentials

1. Click "Credentials" again
2. Click "CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: **Web application**
4. Name: "Django App OAuth"
5. Under "Authorized redirect URIs", add:
   - `http://localhost:8000/accounts/google/login/callback/` (development)
   - `https://yourdomain.com/accounts/google/login/callback/` (production)
6. Click "CREATE"
7. Copy the Client ID and Client Secret from the popup

**Example credentials:**
```
Client ID: 1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxxxxxxxx
```

---

## Part 2: Django Configuration

### Step 1: Install django-allauth

Already done in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 2: Update Django Settings

Already configured in `clinic_project/settings.py`:
- ✓ Added apps to INSTALLED_APPS
- ✓ Added AUTHENTICATION_BACKENDS
- ✓ Set SITE_ID = 1
- ✓ Configured allauth settings
- ✓ Set up Google OAuth provider

### Step 3: Update URLs

Already configured in `clinic_project/urls.py`:
```python
path('accounts/', include('allauth.urls')),
```

This provides:
- `/accounts/login/` — Login page
- `/accounts/logout/` — Logout
- `/accounts/signup/` — Signup (optional)
- `/accounts/google/login/callback/` — OAuth callback (automatic)

### Step 4: Update .env File

Copy the credentials from Google Cloud Console to your `.env`:

```env
# Google OAuth Credentials (from Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxx

# Redirect URI (must match Google Cloud Console)
GOOGLE_OAUTH_CALLBACK_URL=http://localhost:8000/accounts/google/login/callback/
```

---

## Part 3: Database Setup

### Step 1: Apply Migrations

```bash
python manage.py migrate
```

This creates tables for:
- `django.contrib.sites` — Site framework (required by allauth)
- `allauth` — User social accounts
- `socialaccount` — OAuth provider connections

### Step 2: Configure Google OAuth App in Django

Run the setup command:

```bash
python manage.py setup_google_oauth
```

This automatically:
- Creates the Site record (required by django-allauth)
- Registers Google OAuth app
- Associates it with your site

**You should see:**
```
✓ Site: OkiDoki Clinic (localhost:8000)
✓ Created Google OAuth App
✓ Google OAuth Setup Complete!
```

If credentials are not in `.env`, provide them manually:

```bash
python manage.py setup_google_oauth \
  --client-id 1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com \
  --secret GOCSPX-xxxxxxxxxxxxxxxxxxx
```

---

## Part 4: Testing

### Step 1: Start Django Server

```bash
python manage.py runserver
```

### Step 2: Visit Login Page

Open: `http://localhost:8000/accounts/login/`

You should see:
- Email/password login form
- "Sign Up" link
- **"Google" button** ← Click this!

### Step 3: Test Google Sign-In

1. Click the Google button
2. You'll be redirected to Google login (if not already logged in)
3. Google asks for permission to access email/profile
4. Click "Allow"
5. Redirected back to your app, logged in!
6. Redirected to `/dashboard/` (or configured LOGIN_REDIRECT_URL)

### Step 4: Check User Created

In Django admin (`/admin/`):
1. Go to "Users" (auth.User)
2. New user created with email as username
3. Go to "Social accounts" (socialaccount.SocialAccount)
4. Google connection linked to the user

---

## Part 5: Customization

### Create Custom Login Template

Create `templates/account/login.html`:

```html
{% extends "base.html" %}
{% load socialaccount %}

{% block content %}
<div class="login-container">
    <h1>Sign In to OkiDoki Clinic</h1>
    
    <!-- Google OAuth Button -->
    <a href="{% provider_login_url 'google' %}" class="btn btn-primary">
        <img src="/static/images/google-logo.png" alt="Google" width="20">
        Sign in with Google
    </a>
    
    <!-- Or Email/Password -->
    <form method="post">
        {% csrf_token %}
        <!-- Email/password form -->
    </form>
</div>
{% endblock %}
```

### Redirect After Login

In `settings.py`, the redirect is already configured:

```python
LOGIN_REDIRECT_URL = '/dashboard/'
```

After successful OAuth, users are redirected to their dashboard.

### Link Existing Accounts

If a user has both Google and email/password accounts, allauth automatically links them if:
- Email addresses match
- `SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'` (already set)

---

## Part 6: Production Deployment

### Step 1: Update Google Cloud Console

Add production redirect URI:

```
https://yourdomain.com/accounts/google/login/callback/
```

### Step 2: Update .env

```env
GOOGLE_OAUTH_CLIENT_ID=your-prod-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-prod-secret
GOOGLE_OAUTH_CALLBACK_URL=https://yourdomain.com/accounts/google/login/callback/
```

### Step 3: Update Django Site

In Django admin:
1. Go to "Sites" (from django.contrib.sites)
2. Edit site with ID=1
3. Set Domain to: `yourdomain.com`
4. Set Name to: `OkiDoki Clinic`

Or use management command:

```bash
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> site = Site.objects.get(id=1)
>>> site.domain = 'yourdomain.com'
>>> site.name = 'OkiDoki Clinic'
>>> site.save()
```

### Step 4: Set DEBUG = False

```env
DEBUG=False
```

### Step 5: Configure ALLOWED_HOSTS

```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

---

## Troubleshooting

### ❌ "Redirect URI mismatch" Error

**Issue:** Google says the redirect URI doesn't match.

**Fix:**
1. Check exact URI in Google Cloud Console
2. Check exact URI in Django settings
3. They must match EXACTLY (including protocol and port)

**Examples:**
```
✓ http://localhost:8000/accounts/google/login/callback/
✗ http://localhost:8000/accounts/google/login/callback  (no trailing slash)
✗ http://localhost:8000/accounts/google/login  (wrong path)
```

### ❌ "Invalid client id" Error

**Issue:** Client ID is missing or wrong.

**Fix:**
1. Check `.env` has GOOGLE_OAUTH_CLIENT_ID set
2. Verify Client ID from Google Cloud Console
3. Run: `python manage.py setup_google_oauth` to verify it's loaded

### ❌ Google Button Not Showing

**Issue:** "Sign in with Google" button not visible on login page.

**Possible causes:**
1. Custom login template not loading allauth tags
2. Site not properly configured (check `django.contrib.sites`)
3. SocialApp not created (run setup command)

**Fix:**
```html
{% load socialaccount %}
<a href="{% provider_login_url 'google' %}">Sign in with Google</a>
```

### ❌ "No such table: socialaccount_socialapp"

**Issue:** Database tables not created.

**Fix:**
```bash
python manage.py migrate
```

### ❌ User Created But Not Logged In

**Issue:** User created but redirected to login page again.

**Likely cause:** Session not working properly.

**Fix:**
1. Check `SESSION_ENGINE` in settings (should be default django session backend)
2. Verify database migrations ran: `python manage.py migrate`
3. Clear browser cookies and try again

---

## Security Best Practices

### 1. Environment Variables

ALWAYS store credentials in `.env`:
```env
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
```

NEVER commit credentials to git!

### 2. HTTPS in Production

Google requires HTTPS for OAuth:
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### 3. Email Verification

Already configured:
```python
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'mandatory'
```

### 4. Token Storage

Tokens are stored securely in database:
```python
SOCIALACCOUNT_STORE_TOKENS = True
```

---

## API Integration (Optional)

Once signed in with Google, you can use the stored token to access Google APIs:

```python
from allauth.socialaccount.models import SocialAccount

user = request.user
google_account = SocialAccount.objects.get(user=user, provider='google')
access_token = google_account.socialtoken_set.first().token

# Use access_token for Google Calendar API, etc.
```

---

## Management Commands

### Setup Google OAuth

```bash
# Read from .env
python manage.py setup_google_oauth

# Or provide credentials directly
python manage.py setup_google_oauth --client-id YOUR_ID --secret YOUR_SECRET
```

### Verify Setup

```bash
python manage.py shell
>>> from allauth.socialaccount.models import SocialApp
>>> SocialApp.objects.get(provider='google')
<SocialApp: Google OAuth>
```

---

## File Reference

| File | Changes |
|------|---------|
| `requirements.txt` | Added django-allauth |
| `clinic_project/settings.py` | Added apps, backends, allauth config |
| `clinic_project/urls.py` | Added allauth URLs |
| `.env.example` | Added Google OAuth credentials |
| `appointments/management/commands/setup_google_oauth.py` | NEW: Setup command |

---

## Quick Checklist

- [ ] Google Cloud Project created
- [ ] Google+ API enabled
- [ ] OAuth 2.0 credentials created
- [ ] Client ID and Secret copied
- [ ] Updated .env with credentials
- [ ] Ran migrations: `python manage.py migrate`
- [ ] Ran setup command: `python manage.py setup_google_oauth`
- [ ] Updated Site domain in Django admin
- [ ] Tested at `/accounts/login/`
- [ ] Google button visible and working
- [ ] User can sign in with Google

---

## Next Steps

1. **Customize login page** — Create branded login template
2. **Add user profile** — Store additional info from Google (phone, avatar)
3. **Connect to patient system** — Link Google accounts to Patient profiles
4. **Production deployment** — Update credentials and domain
5. **Optional: Link to Google Calendar** — Use stored token for appointment sync

---

**For questions, check the [Configuration Reference](EMAIL_REMINDERS_CONFIGURATION_REFERENCE.md) or Django-Allauth [official docs](https://django-allauth.readthedocs.io/)**

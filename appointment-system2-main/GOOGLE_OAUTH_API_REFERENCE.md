# Google OAuth API Endpoints & Configuration Reference

Complete API endpoint reference and configuration checklist for Google OAuth integration.

---

## Authentication Endpoints

### Login & Logout

| Endpoint | Method | Purpose | Template |
|----------|--------|---------|----------|
| `/accounts/login/` | GET, POST | User login page | `templates/account/login.html` ✅ |
| `/accounts/logout/` | GET, POST | Log out user | (Django allauth built-in) |
| `/accounts/signup/` | GET, POST | User registration | (Django allauth built-in) |
| `/accounts/password/reset/` | GET, POST | Reset password | (Django allauth built-in) |

### Google OAuth Flow

| Endpoint | Method | Purpose | Redirects |
|----------|--------|---------|-----------|
| `/accounts/google/login/` | GET | Start Google OAuth | → Google login screen |
| `/accounts/google/login/callback/` | GET | OAuth callback | ← From Google, → Dashboard |
| `/accounts/google/disconnect/` | POST | Disconnect Google account | → Account settings |

### Account Management

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---|
| `/accounts/email/` | GET, POST | Manage emails | ✅ Yes |
| `/accounts/password/change/` | GET, POST | Change password | ✅ Yes |
| `/accounts/social/connections/` | GET | View OAuth connections | ✅ Yes |

---

## Django Settings Configuration

### Required Settings

✅ All implemented in `clinic_project/settings.py`:

```python
# Database
DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'

# Django Sites (required for allauth)
INSTALLED_APPS = [
    ...
    'django.contrib.sites',
]
SITE_ID = 1

# Django-Allauth
INSTALLED_APPS = [
    ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Account Configuration
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True

# Social Account Configuration
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_OAUTH_CLIENT_ID', default=''),
            'secret': config('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}

# Login Redirects (already configured)
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
```

### Environment Variables

**Required in .env:**

```env
# Google OAuth Credentials
GOOGLE_OAUTH_CLIENT_ID=1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-secret-from-google-cloud
GOOGLE_OAUTH_CALLBACK_URL=http://localhost:8000/accounts/google/login/callback/
```

---

## URL Routing Configuration

**File:** `clinic_project/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # ✅ Provides all OAuth routes
    path('', include('appointments.urls')),
]
```

**Routes automatically provided by `allauth.urls`:**

```
accounts/        → allauth.account
├── login/              [GET, POST]   → account_login
├── logout/             [GET, POST]   → account_logout
├── signup/             [GET, POST]   → account_signup
├── email/              [GET, POST]   → account_email
├── password/change/    [GET, POST]   → account_change_password
├── password/reset/     [GET, POST]   → account_reset_password
├── password/reset/done/               → account_reset_password_done
│
├── google/
│   ├── login/          [GET]   → google_login (redirect to Google)
│   ├── login/callback/ [GET]   → google_callback (OAuth callback)
│   └── disconnect/     [POST]  → socialaccount_disconnect
│
└── social/
    ├── connections/    [GET]   → socialaccount_connections
    └── ...
```

---

## Login Template Tag Reference

**File:** `templates/account/login.html`

### Required Imports

```html
{% load socialaccount %}
```

### Provider Login URL

```html
<!-- Generic provider link -->
<a href="{% provider_login_url 'google' %}">Sign in with Google</a>

<!-- With next redirect -->
<a href="{% provider_login_url 'google' next=request.GET.next %}">
    Sign in with Google
</a>
```

### Check if User Has Social Account

```html
{% load socialaccount %}
{% if request.user.socialaccount_set.all %}
    <p>Connected accounts:</p>
    {% for account in request.user.socialaccount_set.all %}
        <p>{{ account.provider }}: {{ account.display_name }}</p>
    {% endfor %}
{% endif %}
```

### Get User's Google Profile Data

```python
# In views.py
from allauth.socialaccount.models import SocialAccount

user = request.user
google_account = SocialAccount.objects.filter(user=user, provider='google').first()
if google_account:
    extra_data = google_account.extra_data  # dict with profile info
    # {
    #     'email': 'user@gmail.com',
    #     'name': 'John Doe',
    #     'picture': 'https://...',
    #     'locale': 'en',
    #     ...
    # }
```

---

## Database Schema

### django.contrib.sites

```sql
CREATE TABLE django_site (
    id INT PRIMARY KEY,
    domain VARCHAR(100) UNIQUE,  -- 'localhost:8000' or 'yourdomain.com'
    name VARCHAR(50)              -- 'OkiDoki Clinic'
);

-- Required record:
INSERT INTO django_site (id, domain, name) 
VALUES (1, 'localhost:8000', 'OkiDoki Clinic');
```

### socialaccount_socialapp

```sql
CREATE TABLE socialaccount_socialapp (
    id INT PRIMARY KEY,
    provider VARCHAR(30),         -- 'google'
    name VARCHAR(40),             -- 'Google OAuth'
    client_id VARCHAR(191) UNIQUE,
    secret VARCHAR(191),
    created_at DATETIME
);

-- Google OAuth app record (created by setup_google_oauth.py):
INSERT INTO socialaccount_socialapp (provider, name, client_id, secret)
VALUES ('google', 'Google OAuth', '1037934508679-...', 'GOCSPX-...');
```

### socialaccount_socialapp_sites

```sql
-- Join table: associates apps with sites
CREATE TABLE socialaccount_socialapp_sites (
    id INT PRIMARY KEY,
    socialapp_id INT,
    site_id INT
);
```

### socialaccount_socialaccount

```sql
-- User's connected social accounts
CREATE TABLE socialaccount_socialaccount (
    id INT PRIMARY KEY,
    user_id INT,
    provider VARCHAR(30),  -- 'google'
    uid VARCHAR(255),      -- Google user ID
    last_login DATETIME,
    date_joined DATETIME,
    extra_data LONGTEXT    -- JSON: {email, name, picture, ...}
);
```

### socialaccount_socialtoken

```sql
-- OAuth tokens for API access
CREATE TABLE socialaccount_socialtoken (
    id INT PRIMARY KEY,
    socialaccount_id INT,
    token LONGTEXT,
    token_secret TEXT,
    expires_at DATETIME
);
```

---

## Management Commands

### Setup Google OAuth App

```bash
# Read credentials from .env
python manage.py setup_google_oauth

# Provide credentials directly
python manage.py setup_google_oauth \
  --client-id 1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com \
  --secret GOCSPX-xxxxxxxxxxxxxxxxxxx
```

**Output:**
```
======================================================================
Google OAuth Setup for django-allauth
======================================================================

✓ Site: OkiDoki Clinic (localhost:8000)
✓ Created Google OAuth App
✓ Google OAuth Setup Complete!

Next Steps:
  1. Update .env with GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET
  2. In Google Cloud Console, add this Redirect URI:
     http://localhost:8000/accounts/google/login/callback/
  3. Visit /accounts/login/ to test Google sign-in
```

---

## HTTP Request/Response Examples

### 1. User Clicks "Sign in with Google"

```
GET /accounts/google/login/ HTTP/1.1
Host: localhost:8000

→ Redirects to:
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=1037934508679-...
  scope=profile%20email
  redirect_uri=http://localhost:8000/accounts/google/login/callback/
  response_type=code
  access_type=online
```

### 2. Google Redirects Back After User Approves

```
GET /accounts/google/login/callback/?code=4/0AY22...&state=... HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...

Processing:
1. Extract authorization code
2. POST to Google API endpoint with code
3. Receive access token
4. Fetch user profile (email, name, picture)
5. Create/authenticate Django user
6. Create session

→ Redirects to:
/dashboard/ (or LOGIN_REDIRECT_URL)
Set-Cookie: sessionid=...
```

### 3. Subsequent Authenticated Requests

```
GET /dashboard/ HTTP/1.1
Host: localhost:8000
Cookie: sessionid=...

Response includes:
request.user = <User: user@gmail.com>
request.user.is_authenticated = True
request.user.socialaccount_set.all() = [GoogleAccount]
```

---

## OAuth Flow Sequence Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ User Browser at http://localhost:8000/accounts/login/        │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ Click "Sign in with Google"
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ Django App                                                    │
│ GET /accounts/google/login/                                  │
│ → Generate state parameter                                   │
│ → Redirect to Google OAuth endpoint                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ Google OAuth Server                                           │
│ /o/oauth2/v2/auth?client_id=...&redirect_uri=...            │
│ → Show login/consent screen                                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ User logs in & approves
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ Django App                                                    │
│ GET /accounts/google/login/callback/?code=...&state=...     │
│ → Verify state parameter                                    │
│ → Exchange code for access token                            │
│ → Fetch user profile                                        │
│ → Create/authenticate Django user                          │
│ → Create session                                            │
│ → Redirect to /dashboard/                                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ Dashboard - User is logged in ✓                              │
│ request.user = <User: user@gmail.com>                       │
│ request.user.is_authenticated = True                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Integration Test Checklist

- [ ] Site record exists with ID=1
- [ ] Google OAuth app registered in Django admin
- [ ] Credentials in .env match Google Cloud Console
- [ ] Login page shows Google button
- [ ] Clicking button redirects to Google
- [ ] Logging in with Google redirects back
- [ ] User created in Django with correct email
- [ ] Session created and user is authenticated
- [ ] SocialAccount record created
- [ ] Redirected to dashboard after login
- [ ] Can log out
- [ ] Can log back in with same Google account

---

## Configuration Comparison

### Local Development

```
Domain: localhost:8000
Redirect URI: http://localhost:8000/accounts/google/login/callback/
DEBUG: True
HTTPS: Not required
```

### Production

```
Domain: yourdomain.com
Redirect URI: https://yourdomain.com/accounts/google/login/callback/
DEBUG: False
HTTPS: Required (Google enforces)
```

---

## Performance Considerations

- **First Login:** ~2-3 seconds (includes Google redirect and token exchange)
- **Cached Sessions:** ~100ms (subsequent requests with valid session)
- **Token Refresh:** Automatic (happens in background if enabled)
- **Database Queries:** 3-4 queries per login

---

## Security Checklist

✅ Environment variables for secrets
✅ CSRF protection (allauth handles)
✅ State parameter verification (allauth handles)
✅ Secure token storage
✅ HTTPS required for production
✅ SameSite cookies
✅ Email verification available

---

## Version Information

- **Django:** 4.2+
- **Django-Allauth:** 0.56.0+
- **Python:** 3.8+
- **Database:** MySQL 5.7+ (or compatible)

---

## Resources

- [Django-Allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Setup Guide](GOOGLE_OAUTH_SETUP_GUIDE.md)
- [Quick Start](GOOGLE_OAUTH_QUICK_START.md)
- [Implementation Summary](GOOGLE_OAUTH_IMPLEMENTATION_SUMMARY.md)

# Google OAuth Quick Start

Get Google OAuth sign-in working in 5 minutes.

---

## 1. Add Credentials to .env

```env
GOOGLE_OAUTH_CLIENT_ID=1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-secret-from-google-cloud-console
GOOGLE_OAUTH_CALLBACK_URL=http://localhost:8000/accounts/google/login/callback/
```

---

## 2. Prepare Database

```bash
# Install migrations (django.contrib.sites, allauth tables)
python manage.py migrate

# Create superuser if not already done
python manage.py createsuperuser
```

---

## 3. Configure Google OAuth App

```bash
# Option A: Auto-setup from .env
python manage.py setup_google_oauth

# Option B: Manual setup with credentials
python manage.py setup_google_oauth \
  --client-id 1037934508679-lgmm56eg0ac0sj0ld4paqg7525gi8n0c.apps.googleusercontent.com \
  --secret GOCSPX-xxxxxxxxxxxxxxxxxxx
```

---

## 4. Start Server & Test

```bash
python manage.py runserver
```

Visit: **http://localhost:8000/accounts/login/**

You should see:
- "Sign in with Google" button ✓
- Email/password login ✓
- "Sign up" link ✓

---

## 5. Test Google Sign-In

1. Click "Sign in with Google"
2. Log in with your Google account
3. Allow permissions
4. You should be logged in and redirected to dashboard ✓

---

## Verify Setup

Check Django admin:

```bash
python manage.py shell
```

```python
# Verify Site is configured
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
print(f"Site: {site.name} ({site.domain})")

# Verify Google OAuth App is registered
from allauth.socialaccount.models import SocialApp
app = SocialApp.objects.get(provider='google')
print(f"Google App: {app.name}")
print(f"Client ID: {app.client_id}")
print(f"Associated sites: {list(app.sites.all())}")
```

---

## Troubleshooting

### Issue: Google button not showing
- Check: `templates/account/login.html` exists
- Fix: Ensure `{% load socialaccount %}` at top of template

### Issue: "Redirect URI mismatch"
- Check: Exact URI in Google Cloud Console matches GOOGLE_OAUTH_CALLBACK_URL
- Both must include trailing slash: `/accounts/google/login/callback/`

### Issue: "No such table: socialaccount_socialapp"
- Fix: Run `python manage.py migrate`

### Issue: Can't log in
- Check: `.env` has GOOGLE_OAUTH_CLIENT_ID set
- Fix: Run setup command again

---

## Full Setup Guide

For detailed instructions, see: **[GOOGLE_OAUTH_SETUP_GUIDE.md](GOOGLE_OAUTH_SETUP_GUIDE.md)**

---

## Configuration Files Changed

| File | What Changed |
|------|--------------|
| `requirements.txt` | Added django-allauth>=0.56.0 |
| `clinic_project/settings.py` | Added authentication backends, Site ID, allauth config, Google provider |
| `clinic_project/urls.py` | Added `path('accounts/', include('allauth.urls'))` |
| `.env.example` | Added GOOGLE_OAUTH_CLIENT_ID, CLIENT_SECRET, CALLBACK_URL |
| `templates/account/login.html` | NEW: Login page with Google button |
| `appointments/management/commands/setup_google_oauth.py` | NEW: Setup management command |

---

## Next Steps After Basic Setup

1. **Update Site Domain** — In Django admin, change Site domain to your production domain
2. **Customize Templates** — Update login/signup templates for branding
3. **Link to Patient Profile** — Connect Google OAuth to existing Patient model
4. **Production Deployment** — Update credentials and redirect URIs for production domain
5. **Email Verification** — Optional: set `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`

---

For Google Cloud Console setup, see: **[Part 1 of Setup Guide](GOOGLE_OAUTH_SETUP_GUIDE.md#part-1-google-cloud-console-setup)**

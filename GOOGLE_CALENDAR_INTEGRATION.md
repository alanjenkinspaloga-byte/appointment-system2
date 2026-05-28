# Google Calendar Integration - Setup Guide

## Overview

This document explains how to set up and use Google Calendar integration with the Appointment System to automatically create Google Meet links for online consultations.

## Features

- ✅ OAuth 2.0 authentication with Google
- ✅ Automatic Google Calendar event creation
- ✅ Auto-generated Google Meet video conference links
- ✅ Email notifications to both doctor and patient
- ✅ Seamless integration with existing appointment system
- ✅ Secure token storage and refresh

## Prerequisites

1. **Google Account**: A personal or business Google account
2. **Google Cloud Console Access**: https://console.cloud.google.com
3. **Project Setup**: A Google Cloud project with Calendar API enabled
4. **OAuth Credentials**: OAuth 2.0 Desktop application credentials

## Setup Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click **NEW PROJECT**
4. Enter a project name: `Appointment System` or similar
5. Click **CREATE**

### Step 2: Enable Google Calendar API

1. In the Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click on **Google Calendar API**
4. Click **ENABLE**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, click **Configure Consent Screen**
   - **User Type**: Select "External"
   - **App name**: "Appointment System"
   - **User support email**: Your email
   - **Developer contact**: Your email
   - Click **SAVE AND CONTINUE**
4. Back on the credentials page, click **+ CREATE CREDENTIALS** → **OAuth client ID** again
5. **Application type**: Select "Desktop app" (NOT Web)
6. **Name**: "Appointment System Doctor"
7. Click **CREATE**
8. Click the download button and save as `client_secret_*.json`

### Step 4: Configure the Downloaded Credentials

1. Rename the downloaded file to `google_oauth_credentials.json`
2. Place it in your Django project root directory (same level as `manage.py`)
3. The file should look like this:

```json
{
  "web": {
    "client_id": "YOUR-CLIENT-ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR-CLIENT-SECRET",
    "redirect_uris": [
      "http://localhost:8000/appointments/google-oauth-callback/",
      "https://yourdomain.com/appointments/google-oauth-callback/"
    ],
    "javascript_origins": [
      "http://localhost:8000",
      "https://yourdomain.com"
    ]
  }
}
```

### Step 5: Update Django Settings

The credentials file path is already configured in `settings.py`:

```python
GOOGLE_OAUTH_CREDENTIALS_FILE = config(
    'GOOGLE_OAUTH_CREDENTIALS_FILE',
    default=str(BASE_DIR / 'google_oauth_credentials.json')
)
```

### Step 6: Run Database Migrations

```bash
python manage.py migrate
```

This creates the necessary database fields:
- `Doctor.is_google_calendar_connected`
- `Doctor.google_calendar_token`
- `Appointment.is_online_consultation`
- `Appointment.google_meet_link`
- `Appointment.google_calendar_event_id`

### Step 7: Install Required Python Packages

The following packages are already included in `requirements.txt`:
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth-httplib2`

If not, install them:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## For Doctors: How to Enable Google Meet for Your Appointments

### Connect Your Google Calendar

1. Log in to your doctor account
2. Go to **Doctor Dashboard**
3. Look for the **Google Calendar Integration** section or the **Enable Google Meet** button
4. Click **Connect Google Calendar**
5. You will be redirected to Google's authorization page
6. Review the permissions and click **Allow**
7. You should be redirected back to your dashboard with a success message

### After Connecting

- Your Google Calendar is now connected
- Any appointment marked as "online consultation" will automatically create a Google Meet event
- Both the doctor and patient will receive email invitations with the Meet link
- The Meet link will be saved and displayed in the appointment details

### Disconnect Google Calendar

If you want to disconnect:

1. Go to **Doctor Dashboard**
2. Find the **Google Calendar Integration** section
3. Click the **Disconnect** button
4. Confirm your choice

**Note**: If you disconnect, new online appointments won't create Google Meet links automatically.

## For Patients: Using Google Meet Appointments

### Booking an Online Consultation

1. Find a doctor who offers online consultations
2. Select a date and time
3. Check the **"Online Consultation"** option during booking
4. Complete the booking
5. You will receive an email with the Google Meet link

### Joining the Meeting

1. On the appointment day, go to **My Appointments**
2. Find the appointment
3. Click **Join Google Meet** button or use the provided link
4. The link will open in a new browser tab

## Technical Architecture

### File Structure

```
appointments/
├── google_calendar_utils.py      # Main Calendar API logic
├── google_oauth_views.py          # OAuth authentication views
├── google_calendar_settings.py    # Configuration
├── google_meet_views.py           # Meet link display utilities
├── signals.py                     # Signal handlers (updated)
├── models.py                      # Models (updated with Google fields)
└── urls.py                        # URL routing (updated)

templates/
├── doctor/
│   ├── sidebar.html               # Sidebar (updated with Google Calendar)
│   ├── google_calendar_widget.html # Google Calendar widget
│   └── dashboard.html             # Dashboard (updated)
└── patient/
    ├── sidebar.html               # Sidebar (updated)
    └── google_meet_display.html   # Meet link display

migrations/
└── 0013_google_calendar_integration.py  # Database migration
```

### OAuth Flow

```
Doctor Click "Connect"
          ↓
OAuth Authorization Initiation
          ↓
Google Authorization URL
          ↓
Doctor Grants Permission
          ↓
OAuth Callback Handler
          ↓
Token Exchange
          ↓
Save Encrypted Token to Doctor Model
          ↓
Status: Connected ✓
```

### Appointment Workflow

```
Patient Books Online Appointment
          ↓
Appointment Created (is_online_consultation=True)
          ↓
Admin/Doctor Confirms Appointment
          ↓
Django Signal Triggered
          ↓
Google Calendar Event Created
          ↓
Google Meet Link Generated
          ↓
Link Saved to Appointment Model
          ↓
Email Invitations Sent
          ↓
Doctor & Patient Can Join Meeting
```

## API Integration Details

### Google Calendar API Scope

```python
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
```

This scope allows:
- Creating calendar events
- Updating calendar events
- Reading calendar information
- NOT: Deleting events or managing calendar settings

### Calendar Event Details

When an online appointment is created, the following event is inserted:

```python
{
    'summary': 'Online Consultation - [Patient Name]',
    'description': 'Patient: ...\nDoctor: ...\nSpecialization: ...\nReason: ...',
    'start': {'dateTime': '2026-05-10T14:00:00Z', 'timeZone': 'Asia/Manila'},
    'end': {'dateTime': '2026-05-10T14:30:00Z', 'timeZone': 'Asia/Manila'},
    'attendees': [
        {'email': 'patient@example.com', 'displayName': 'Patient Name'},
        {'email': 'doctor@example.com', 'displayName': 'Dr. Doctor Name'}
    ],
    'conferenceData': {
        'createRequest': {
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            'requestId': 'appointment-123'
        }
    },
    'sendUpdates': 'all'
}
```

### Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Token expired | Token is automatically refreshed |
| 404 Not Found | Calendar not found | Use 'primary' calendar (built-in) |
| 403 Forbidden | Permission denied | Re-authenticate and grant permissions |
| FileNotFoundError | Credentials file missing | Place `google_oauth_credentials.json` in project root |

## Security Considerations

### Token Storage

- OAuth tokens are stored in the `Doctor.google_calendar_token` field as JSON
- **Production**: Encrypt tokens using Django's encryption middleware
- **Development**: Tokens are stored in plain JSON (acceptable for testing only)

### Recommended Production Setup

1. Use environment variables for credentials
2. Encrypt sensitive token data in the database
3. Implement token rotation policies
4. Log all API operations
5. Use HTTPS for OAuth callback

Example `.env` file:

```
GOOGLE_OAUTH_CREDENTIALS_FILE=/path/to/google_oauth_credentials.json
DEBUG=False
SECRET_KEY=your-production-secret-key
```

### Permissions

The application requests minimal necessary permissions:
- `calendar.events` - Only calendar event operations
- NOT calendar admin, email, or other sensitive scopes

## Troubleshooting

### "Credentials file not found"

```
ERROR: Google OAuth credentials file not found at ...
```

**Solution**: 
1. Download credentials from Google Cloud Console
2. Rename to `google_oauth_credentials.json`
3. Place in Django project root directory

### "Invalid OAuth state"

**Solution**: 
1. Clear browser cookies for the domain
2. Try connecting again
3. Make sure redirect URI matches your domain

### Meet link not generating

**Solution**: 
1. Verify doctor has `is_google_calendar_connected = True`
2. Check appointment has `is_online_consultation = True`
3. Check appointment status is 'confirmed'
4. Check Django logs for API errors

### Email invitations not received

**Solution**: 
1. Verify doctor and patient email addresses
2. Check Google Calendar settings for notification preferences
3. Check spam/junk email folders
4. Verify `sendUpdates: 'all'` is enabled in the event

## Advanced Configuration

### Customize Event Duration

In `google_calendar_utils.py`, change the duration:

```python
# Default: 30 minutes
end_time = (event_datetime + timedelta(minutes=30)).isoformat()

# Change to 1 hour
end_time = (event_datetime + timedelta(minutes=60)).isoformat()
```

### Customize Event Description

Modify the `description` field in `create_calendar_event()` method to add custom information.

### Retry Logic

For production, implement retry logic for API failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_calendar_event_with_retry(appointment):
    # Implementation
    pass
```

## Support & Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Google Meet Integration](https://developers.google.com/calendar/api/concepts/events-acls/conferences)
- [Django Security Middleware](https://docs.djangoproject.com/en/stable/topics/security/)

## Version History

- **v1.0** (2026-05-07): Initial release with Google Calendar integration

## License

This integration is part of the Appointment System project.

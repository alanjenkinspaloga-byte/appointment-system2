# ============================================================
# appointments/google_calendar_settings.py
# Google Calendar Configuration & Setup Helper
# ============================================================
"""
Configuration for Google Calendar API integration.

To set up Google Calendar integration:
1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Create a new project
3. Enable Calendar API and Google Meet
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the JSON credentials file
6. Save it as 'google_oauth_credentials.json' in the project root
7. Add the redirect URI to your credentials:
   - http://localhost:8000/appointments/google-oauth-callback/  (development)
   - https://yourdomain.com/appointments/google-oauth-callback/ (production)
"""

import os
from django.conf import settings

# Path to Google OAuth credentials file
GOOGLE_OAUTH_CREDENTIALS_FILE = os.path.join(
    settings.BASE_DIR, 'google_oauth_credentials.json'
)

# Google Calendar scopes required for the application
GOOGLE_CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events'
]

# Google Meet configuration
GOOGLE_MEET_CONFIG = {
    'enabled': True,
    'conference_solution': 'hangoutsMeet',
    'duration_minutes': 30,
    'time_zone': settings.TIME_ZONE or 'UTC',
}

def get_google_oauth_credentials_file():
    """Get the path to the Google OAuth credentials file."""
    if os.path.exists(GOOGLE_OAUTH_CREDENTIALS_FILE):
        return GOOGLE_OAUTH_CREDENTIALS_FILE
    else:
        raise FileNotFoundError(
            f"Google OAuth credentials file not found at {GOOGLE_OAUTH_CREDENTIALS_FILE}. "
            "Please download and save your credentials from Google Cloud Console."
        )

# ============================================================
# appointments/google_oauth_views.py
# Google OAuth Authentication for Doctors
# ============================================================
"""
Handles OAuth 2.0 flow for doctors to authenticate with Google Calendar.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .models import Doctor
from .decorators import doctor_required

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def get_credentials_file():
    """
    Get the path to the OAuth 2.0 credentials JSON file.
    This should be stored in your Django settings or project directory.
    """
    credentials_path = getattr(
        settings, 
        'GOOGLE_OAUTH_CREDENTIALS_FILE',
        'google_oauth_credentials.json'
    )
    return credentials_path


@login_required
@doctor_required
def google_oauth_authorize(request):
    """
    Step 1: Initiate Google OAuth flow.
    Redirects user to Google's authorization server.
    """
    try:
        doctor = request.user.doctor_profile
        
        # Initialize the OAuth flow
        flow = Flow.from_client_secrets_file(
            get_credentials_file(),
            scopes=SCOPES,
            redirect_uri=request.build_absolute_uri('/appointments/google-oauth-callback/'),
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
        )
        
        # Store state in session for verification during callback
        request.session['google_oauth_state'] = state
        request.session['doctor_id'] = doctor.id
        
        logger.info(f"OAuth authorization initiated for doctor {doctor.id}")
        
        return redirect(authorization_url)
        
    except FileNotFoundError:
        messages.error(
            request,
            'Google OAuth credentials file not found. Please contact admin.'
        )
        logger.error("Google OAuth credentials file not found")
        return redirect('doctor_dashboard')
    except Exception as e:
        messages.error(request, f'OAuth authorization error: {str(e)}')
        logger.error(f"OAuth authorization error: {str(e)}")
        return redirect('doctor_dashboard')


@login_required
def google_oauth_callback(request):
    """
    Step 2: Handle OAuth callback from Google.
    Exchanges authorization code for access token.
    """
    try:
        # Verify state parameter
        state = request.session.get('google_oauth_state')
        if not state or state != request.GET.get('state'):
            messages.error(request, 'Invalid OAuth state. Authorization failed.')
            logger.warning("OAuth state mismatch")
            return redirect('doctor_dashboard')
        
        # Get doctor instance
        doctor_id = request.session.get('doctor_id')
        if not doctor_id:
            messages.error(request, 'Doctor session not found.')
            return redirect('doctor_dashboard')
        
        doctor = get_object_or_404(Doctor, id=doctor_id, user=request.user)
        
        # Check for errors from Google
        error = request.GET.get('error')
        if error:
            messages.error(request, f'Authorization failed: {error}')
            logger.warning(f"OAuth error: {error}")
            return redirect('doctor_dashboard')
        
        # Initialize flow
        flow = Flow.from_client_secrets_file(
            get_credentials_file(),
            scopes=SCOPES,
            state=state,
            redirect_uri=request.build_absolute_uri('/appointments/google-oauth-callback/'),
        )
        
        # Exchange code for token
        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)
        
        # Get credentials
        credentials = flow.credentials
        
        # Save credentials to doctor profile
        token_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes),
        }
        
        doctor.google_calendar_token = json.dumps(token_dict)
        doctor.is_google_calendar_connected = True
        doctor.save()
        
        # Clean up session
        del request.session['google_oauth_state']
        if 'doctor_id' in request.session:
            del request.session['doctor_id']
        
        messages.success(
            request,
            'Google Calendar successfully connected! Online appointments will now include Google Meet links.'
        )
        logger.info(f"OAuth token saved for doctor {doctor.id}")
        
        return redirect('doctor_dashboard')
        
    except Exception as e:
        messages.error(request, f'OAuth callback error: {str(e)}')
        logger.error(f"OAuth callback error: {str(e)}")
        return redirect('doctor_dashboard')


@login_required
@doctor_required
@require_http_methods(["POST"])
def disconnect_google_calendar(request):
    """
    Disconnect doctor's Google Calendar account.
    """
    try:
        doctor = request.user.doctor_profile
        doctor.google_calendar_token = None
        doctor.is_google_calendar_connected = False
        doctor.save()
        
        messages.success(request, 'Google Calendar disconnected.')
        logger.info(f"Google Calendar disconnected for doctor {doctor.id}")
        
        return redirect('doctor_dashboard')
        
    except Exception as e:
        messages.error(request, f'Error disconnecting Google Calendar: {str(e)}')
        logger.error(f"Error disconnecting: {str(e)}")
        return redirect('doctor_dashboard')

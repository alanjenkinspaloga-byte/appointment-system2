# ============================================================
# appointments/google_calendar_utils.py
# Google Calendar API Integration for Online Consultations
# ============================================================
"""
Handles Google Calendar API interactions:
- Creating calendar events with Google Meet links
- Managing doctor's calendar credentials
- Storing and retrieving OAuth tokens
"""

import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


class GoogleCalendarService:
    """
    Handles Google Calendar API interactions for a specific doctor.
    """
    
    def __init__(self, doctor):
        """
        Initialize the service with a doctor instance.
        
        Args:
            doctor: Doctor model instance
        """
        self.doctor = doctor
        self.credentials = None
        self.service = None
        self.load_credentials()
    
    def load_credentials(self):
        """
        Load stored credentials from doctor's profile or token storage.
        Handles refresh if token has expired.
        """
        try:
            if hasattr(self.doctor, 'google_calendar_token') and self.doctor.google_calendar_token:
                token_dict = json.loads(self.doctor.google_calendar_token)
                self.credentials = Credentials.from_authorized_user_info(token_dict, SCOPES)
                
                # Refresh if expired
                if self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    # Save the refreshed token
                    self.save_credentials(self.credentials)
            else:
                logger.warning(f"No Google Calendar token for doctor {self.doctor.id}")
                return False
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return False
    
    def save_credentials(self, credentials):
        """
        Save credentials to doctor profile.
        
        Args:
            credentials: Google OAuth2 credentials
        """
        try:
            token_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
            }
            self.doctor.google_calendar_token = json.dumps(token_dict)
            self.doctor.save(update_fields=['google_calendar_token'])
            logger.info(f"Credentials saved for doctor {self.doctor.id}")
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
    
    def create_calendar_event(self, appointment):
        """
        Create a Google Calendar event with a Google Meet link for an appointment.
        
        Args:
            appointment: Appointment model instance
            
        Returns:
            dict: Event details including hangout_link (Meet URL) or None if failed
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return None
        
        try:
            # Prepare event details
            patient = appointment.patient.user
            doctor = appointment.doctor.user
            hospital = appointment.availability.effective_hospital
            
            # Calculate event time
            event_date = appointment.date
            event_time = appointment.appointment_time or datetime.min.time()
            event_datetime = datetime.combine(event_date, event_time)
            
            # Add timezone handling (use UTC by default)
            start_time = event_datetime.isoformat() + 'Z'
            end_time = (event_datetime + timedelta(minutes=30)).isoformat() + 'Z'
            
            # Build event object with conferenceData for Meet
            event = {
                'summary': f'Online Consultation - {patient.get_full_name()}',
                'description': (
                    f'Patient: {patient.get_full_name()}\n'
                    f'Doctor: Dr. {doctor.get_full_name()}\n'
                    f'Specialization: {appointment.doctor.specialization}\n'
                    f'Reason: {appointment.reason or "General Consultation"}\n'
                    f'Hospital: {hospital.name if hospital else "N/A"}\n'
                    f'Appointment ID: #{appointment.id}'
                ),
                'start': {
                    'dateTime': start_time,
                    'timeZone': settings.TIME_ZONE,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': settings.TIME_ZONE,
                },
                'attendees': [
                    {'email': patient.email, 'displayName': patient.get_full_name()},
                    {'email': doctor.email, 'displayName': f'Dr. {doctor.get_full_name()}'},
                ],
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        },
                        'requestId': f'appointment-{appointment.id}',
                    },
                },
                'sendUpdates': 'all',  # Send email invitations
            }
            
            # Create event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
            ).execute()
            
            logger.info(f"Calendar event created for appointment {appointment.id}")
            
            # Extract and return the Meet link
            result = {
                'event_id': created_event.get('id'),
                'hangout_link': created_event.get('hangoutLink'),
                'event_link': created_event.get('htmlLink'),
            }
            
            return result
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            if e.resp.status == 401:
                # Credentials expired
                logger.error(f"Credentials expired for doctor {self.doctor.id}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {str(e)}")
            return None
    
    def is_authenticated(self):
        """Check if doctor has valid Google Calendar authentication."""
        return self.service is not None and self.credentials is not None


def create_google_meet_event(appointment):
    """
    Main function to create a Google Calendar event with Meet link.
    Called when an appointment is confirmed for online consultation.
    
    Args:
        appointment: Appointment model instance
        
    Returns:
        str: Google Meet link URL or None if creation failed
    """
    try:
        service = GoogleCalendarService(appointment.doctor)
        
        if not service.is_authenticated():
            logger.warning(f"Doctor {appointment.doctor.id} not authenticated with Google Calendar")
            return None
        
        result = service.create_calendar_event(appointment)
        
        if result and result.get('hangout_link'):
            return result['hangout_link']
        
        logger.warning(f"No Meet link returned for appointment {appointment.id}")
        return None
        
    except Exception as e:
        logger.error(f"Error in create_google_meet_event: {str(e)}")
        return None

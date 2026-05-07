from .models import Notification, Doctor, Appointment
from django.db.models import Q
from datetime import date


def notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notif_count': unread_count}
    return {'unread_notif_count': 0}


def google_calendar_context(request):
    """
    Add Google Calendar related context to all templates.
    Provides information about connected status and online consultations.
    """
    if not request.user.is_authenticated:
        return {
            'google_calendar_connected': False,
            'google_calendar_enabled': False,
            'active_meetings_count': 0,
            'pending_online_appointments': 0,
        }
    
    context = {
        'google_calendar_connected': False,
        'google_calendar_enabled': False,
        'active_meetings_count': 0,
        'pending_online_appointments': 0,
        'online_appointments_count': 0,
    }
    
    # Check if user is a doctor
    if hasattr(request.user, 'doctor_profile'):
        doctor = request.user.doctor_profile
        context['google_calendar_connected'] = doctor.is_google_calendar_connected
        context['google_calendar_enabled'] = doctor.is_google_calendar_connected
        
        # Count active meetings (in_progress status for today)
        active_meetings = Appointment.objects.filter(
            doctor=doctor,
            is_online_consultation=True,
            status='in_progress',
            date=date.today(),
        ).count()
        context['active_meetings_count'] = active_meetings
        
        # Count pending online appointments
        pending_online = Appointment.objects.filter(
            doctor=doctor,
            is_online_consultation=True,
            status='pending',
        ).count()
        context['pending_online_appointments'] = pending_online
    
    # Check if user is a patient
    if hasattr(request.user, 'patient_profile'):
        patient = request.user.patient_profile
        # Count online appointments for the patient
        online_appts = Appointment.objects.filter(
            patient=patient,
            is_online_consultation=True,
            status__in=['pending', 'confirmed', 'in_progress'],
        ).count()
        context['online_appointments_count'] = online_appts
    
    return context

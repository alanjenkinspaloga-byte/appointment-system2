# ============================================================
# appointments/google_meet_views.py
# Views for displaying Google Meet links in appointments
# ============================================================
"""
Provides utility views and context processors for displaying Google Meet links.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment, Doctor
from .decorators import patient_required, doctor_required


@login_required
def appointment_with_meet_link(request, appointment_id):
    """
    Display appointment details with Google Meet link for online consultations.
    Accessible by both doctor and patient.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Authorization check
    is_doctor = hasattr(request.user, 'doctor_profile') and \
               request.user.doctor_profile.id == appointment.doctor.id
    is_patient = hasattr(request.user, 'patient_profile') and \
                request.user.patient_profile.id == appointment.patient.id
    
    if not (is_doctor or is_patient):
        messages.error(request, 'You do not have access to this appointment.')
        return redirect('dashboard')
    
    context = {
        'appointment': appointment,
        'is_online_consultation': appointment.is_online_consultation,
        'google_meet_link': appointment.google_meet_link,
        'show_meet_button': (
            appointment.is_online_consultation and 
            appointment.google_meet_link and
            appointment.status in ['confirmed', 'in_progress']
        ),
        'is_doctor': is_doctor,
        'is_patient': is_patient,
    }
    
    return render(request, 'appointments/appointment_with_meet.html', context)


def get_google_meet_context(appointment):
    """
    Helper function to get Google Meet link context for templates.
    
    Returns:
        dict: Context containing Google Meet information
    """
    context = {
        'is_online_consultation': appointment.is_online_consultation,
        'google_meet_link': appointment.google_meet_link,
        'show_meet_button': (
            appointment.is_online_consultation and 
            appointment.google_meet_link and
            appointment.status in ['confirmed', 'in_progress']
        ),
        'meet_ready': appointment.google_meet_link is not None,
    }
    return context

# ============================================================
# appointments/email_utils.py
# Email notification utilities
# ============================================================
"""
Utilities for sending email notifications for appointments.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_online_appointment_confirmation_email(appointment):
    """
    Send confirmation email for online appointments with Jitsi link.
    
    Args:
        appointment: Appointment instance
    """
    try:
        patient_user = appointment.patient.user
        doctor_user = appointment.doctor.user
        
        # Prepare context
        context = {
            'patient_name': patient_user.get_full_name() or patient_user.username,
            'doctor_name': doctor_user.get_full_name() or doctor_user.username,
            'appointment': appointment,
            'video_terms_url': settings.SITE_URL + reverse('video_consultation_terms'),
            'appointment_details_url': settings.SITE_URL + reverse('patient_appointment_detail', args=[appointment.id]),
            'reschedule_url': settings.SITE_URL + reverse('patient_appointments'),
        }
        
        # Render HTML email
        html_content = render_to_string('emails/online_appointment_confirmed.html', context)
        
        # Create email
        subject = f"Your Online Appointment Confirmed - Dr. {doctor_user.get_full_name()}"
        text_content = f"""
Hello {context['patient_name']},

Your online video consultation with Dr. {context['doctor_name']} on {appointment.date} at {appointment.appointment_time} has been confirmed.

Queue Number: {"Q#" + str(appointment.queue_number) if appointment.queue_number else "Pending"}

IMPORTANT: Please read the privacy notice at {context['video_terms_url']}

Join your video call here: {appointment.jitsi_meet_link}

Please join 5 minutes before the scheduled time.

---
OkiDoki Healthcare System
support@okidoki.clinic
        """
        
        # Send to patient
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Appointment confirmation email sent to patient {patient_user.email} for appointment {appointment.id}")
        
        # Also send to doctor
        doctor_subject = f"Appointment Confirmed with {patient_user.get_full_name()}"
        doctor_text = f"""
Hello Dr. {context['doctor_name']},

You have a confirmed online video consultation with {context['patient_name']} on {appointment.date} at {appointment.appointment_time}.

Queue Number: {appointment.queue_number or "N/A"}

Join the video call here: {appointment.jitsi_meet_link}

Please join 5 minutes before the scheduled time.

---
OkiDoki Healthcare System
        """
        
        doctor_email = EmailMultiAlternatives(
            subject=doctor_subject,
            body=doctor_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[doctor_user.email],
        )
        doctor_email.send()
        
        logger.info(f"Appointment confirmation email sent to doctor {doctor_user.email} for appointment {appointment.id}")
        
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email for appointment {appointment.id}: {str(e)}")
        raise


def send_in_person_appointment_confirmation_email(appointment):
    """
    Send confirmation email for in-person appointments.
    
    Args:
        appointment: Appointment instance
    """
    try:
        patient_user = appointment.patient.user
        doctor_user = appointment.doctor.user
        
        # Prepare text content
        text_content = f"""
Hello {patient_user.get_full_name() or patient_user.username},

Your in-person appointment with Dr. {doctor_user.get_full_name()} on {appointment.date} at {appointment.appointment_time} has been confirmed.

Queue Number: {"Q#" + str(appointment.queue_number) if appointment.queue_number else "Pending"}

Location: {appointment.doctor.hospital.name if appointment.doctor.hospital else "N/A"}
Address: {appointment.doctor.hospital.address if appointment.doctor.hospital else "N/A"}

Please arrive 5-10 minutes early.

---
OkiDoki Healthcare System
support@okidoki.clinic
        """
        
        subject = f"Your In-Person Appointment Confirmed - Dr. {doctor_user.get_full_name()}"
        
        # Send email
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[patient_user.email],
            fail_silently=False,
        )
        
        logger.info(f"In-person appointment confirmation email sent to {patient_user.email}")
        
    except Exception as e:
        logger.error(f"Error sending in-person appointment confirmation email: {str(e)}")
        raise

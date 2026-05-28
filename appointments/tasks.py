# ============================================================
# appointments/tasks.py
# Celery Tasks for Email Notifications & Reminders
# ============================================================
"""
Asynchronous tasks handled by Celery worker.
Sends timed email reminders and queue notifications for appointments.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# ============================================================
# REMINDER EMAIL TASKS
# ============================================================

@shared_task(bind=True, max_retries=3)
def send_appointment_reminder(self, appointment_id):
    """
    Send reminder email for a specific appointment.
    
    This task is called when an appointment's reminder time is reached.
    It can be triggered by:
    1. Celery Beat periodic task checking for due reminders
    2. Manually scheduled with a countdown/eta
    
    Args:
        appointment_id: ID of the appointment to send reminder for
        
    Returns:
        dict: Result status with sent_to, timestamp, etc.
    """
    try:
        from appointments.models import Appointment
        
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Verify appointment is still valid for reminder
        if appointment.status in ['cancelled', 'done']:
            logger.warning(
                f"Skipping reminder for appointment {appointment_id}: status={appointment.status}"
            )
            return {
                'status': 'skipped',
                'reason': f'Appointment status is {appointment.status}',
                'appointment_id': appointment_id,
            }
        
        # Skip if reminder already sent
        if appointment.reminder_sent_at:
            logger.info(f"Reminder already sent for appointment {appointment_id}")
            return {
                'status': 'already_sent',
                'sent_at': appointment.reminder_sent_at.isoformat(),
                'appointment_id': appointment_id,
            }
        
        # Send the reminder email
        _send_reminder_email_to_patient(appointment)
        
        # Update appointment to mark reminder as sent
        appointment.reminder_sent_at = timezone.now()
        appointment.save(update_fields=['reminder_sent_at'])
        
        logger.info(f"Reminder email sent for appointment {appointment_id}")
        
        return {
            'status': 'sent',
            'appointment_id': appointment_id,
            'patient_email': appointment.patient.user.email,
            'reminder_time': appointment.get_reminder_datetime().isoformat(),
            'appointment_time': appointment.get_appointment_datetime().isoformat(),
        }
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {
            'status': 'error',
            'error': 'Appointment not found',
            'appointment_id': appointment_id,
        }
    except Exception as exc:
        logger.error(
            f"Error sending reminder for appointment {appointment_id}: {str(exc)}"
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_due_appointment_reminders():
    """
    Periodic task that finds all appointments due for reminders and sends them.
    
    This task runs every 5 minutes (as configured in celery.py beat_schedule).
    It queries for appointments where:
    - Status is 'confirmed' or 'pending'
    - Reminder hasn't been sent yet
    - Current time >= reminder time
    
    Returns:
        dict: Summary of sent reminders
    """
    from appointments.models import Appointment
    
    now = timezone.now()
    
    # Find appointments due for reminders
    due_appointments = Appointment.objects.filter(
        status__in=['confirmed', 'pending'],
        reminder_sent_at__isnull=True,
    ).select_related('patient__user', 'doctor__user', 'doctor__hospital')
    
    sent_count = 0
    error_count = 0
    skipped_count = 0
    
    for appointment in due_appointments:
        reminder_time = appointment.get_reminder_datetime()
        
        # Check if reminder time has been reached
        if reminder_time and reminder_time <= now:
            try:
                # Send the reminder email directly
                _send_reminder_email_to_patient(appointment)
                
                # Mark as sent
                appointment.reminder_sent_at = now
                appointment.save(update_fields=['reminder_sent_at'])
                
                sent_count += 1
                logger.info(
                    f"Sent reminder for appointment {appointment.id} "
                    f"(patient: {appointment.patient.user.email})"
                )
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Failed to send reminder for appointment {appointment.id}: {str(e)}"
                )
        else:
            skipped_count += 1
    
    summary = {
        'task': 'send_due_appointment_reminders',
        'timestamp': now.isoformat(),
        'sent': sent_count,
        'errors': error_count,
        'skipped': skipped_count,
    }
    
    logger.info(f"Periodic reminder check complete: {summary}")
    return summary


@shared_task(bind=True, max_retries=3)
def send_next_in_queue_notification(self, appointment_id):
    """
    Send email to patient notifying they are next in queue.
    
    This task is triggered when the current appointment status changes to 'in_progress',
    notifying the next patient in the queue.
    
    Args:
        appointment_id: ID of the NEXT appointment (patient to notify)
        
    Returns:
        dict: Result status
    """
    try:
        from appointments.models import Appointment
        
        appointment = Appointment.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__hospital'
        ).get(id=appointment_id)
        
        # Check if already sent
        if appointment.next_in_queue_notification_sent:
            logger.info(
                f"Next-in-queue notification already sent for appointment {appointment_id}"
            )
            return {
                'status': 'already_sent',
                'appointment_id': appointment_id,
            }
        
        # Send the notification
        _send_next_in_queue_email(appointment)
        
        # Mark as sent
        appointment.next_in_queue_notification_sent = True
        appointment.save(update_fields=['next_in_queue_notification_sent'])
        
        logger.info(f"Next-in-queue notification sent for appointment {appointment_id}")
        
        return {
            'status': 'sent',
            'appointment_id': appointment_id,
            'patient_email': appointment.patient.user.email,
            'queue_number': appointment.queue_number,
        }
        
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {
            'status': 'error',
            'error': 'Appointment not found',
            'appointment_id': appointment_id,
        }
    except Exception as exc:
        logger.error(
            f"Error sending next-in-queue notification for appointment {appointment_id}: {str(exc)}"
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_expired_reminder_tasks():
    """
    Cleanup task that runs daily (at 2 AM).
    Removes scheduled task IDs for completed/cancelled appointments.
    
    Returns:
        dict: Cleanup summary
    """
    from appointments.models import Appointment
    
    # Clear task IDs for completed/cancelled appointments
    cleared = Appointment.objects.filter(
        status__in=['done', 'cancelled'],
        scheduled_task_id__isnull=False,
    ).update(scheduled_task_id=None)
    
    logger.info(f"Cleanup: Cleared {cleared} expired reminder task IDs")
    
    return {
        'task': 'cleanup_expired_reminder_tasks',
        'cleared_count': cleared,
        'timestamp': timezone.now().isoformat(),
    }


# ============================================================
# HELPER FUNCTIONS FOR EMAIL SENDING
# ============================================================

def _send_reminder_email_to_patient(appointment):
    """
    Send reminder email to patient.
    
    Args:
        appointment: Appointment instance
    """
    try:
        patient_user = appointment.patient.user
        doctor_user = appointment.doctor.user
        doctor_name = doctor_user.get_full_name() or doctor_user.username
        patient_name = patient_user.get_full_name() or patient_user.username
        
        # Calculate time until appointment
        from datetime import datetime
        appt_datetime = appointment.get_appointment_datetime()
        now = timezone.now()
        time_diff = appt_datetime - now
        
        minutes_left = int(time_diff.total_seconds() / 60)
        hours_left = minutes_left // 60
        
        if hours_left > 0:
            time_str = f"{hours_left} hour{'s' if hours_left != 1 else ''} and {minutes_left % 60} minutes"
        else:
            time_str = f"{minutes_left} minute{'s' if minutes_left != 1 else ''}"
        
        # Prepare context
        context = {
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'appointment': appointment,
            'appointment_time': appointment.get_appointment_datetime(),
            'time_until_appointment': time_str,
            'hospital_name': appointment.doctor.hospital.name if appointment.doctor.hospital else 'the clinic',
            'hospital_address': appointment.doctor.hospital.address if appointment.doctor.hospital else '',
            'appointment_details_url': settings.SITE_URL + reverse('patient_appointment_detail', args=[appointment.id]),
            'queue_number': appointment.queue_number or 'N/A',
            'is_online': appointment.is_online_consultation,
            'jitsi_link': appointment.jitsi_meet_link,
        }
        
        # Render HTML email
        if appointment.is_online_consultation:
            html_content = render_to_string('emails/appointment_reminder_online.html', context)
            subject = f"Reminder: Your Online Appointment with Dr. {doctor_name} in {time_str}"
        else:
            html_content = render_to_string('emails/appointment_reminder_inperson.html', context)
            subject = f"Reminder: Your Appointment with Dr. {doctor_name} in {time_str}"
        
        # Plain text version
        text_content = f"""
Hello {patient_name},

This is a reminder that your appointment with Dr. {doctor_name} is coming up in {time_str}.

Date: {appointment.date}
Time: {appointment.appointment_time}
Queue Number: Q#{appointment.queue_number if appointment.queue_number else 'N/A'}

Location: {context['hospital_name']}
{f"Address: {context['hospital_address']}" if context['hospital_address'] else ""}

{"Video Call Link: " + appointment.jitsi_meet_link if appointment.is_online_consultation else "Please arrive 5-10 minutes early."}

View your appointment details: {context['appointment_details_url']}

---
OkiDoki Healthcare System
support@okidoki.clinic
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"Reminder email sent to {patient_user.email} for appointment {appointment.id}"
        )
        
    except Exception as e:
        logger.error(
            f"Error sending reminder email for appointment {appointment.id}: {str(e)}"
        )
        raise


def _send_next_in_queue_email(appointment):
    """
    Send "you are next in queue" email to patient.
    
    Args:
        appointment: Appointment instance (the next one in queue)
    """
    try:
        patient_user = appointment.patient.user
        doctor_user = appointment.doctor.user
        doctor_name = doctor_user.get_full_name() or doctor_user.username
        patient_name = patient_user.get_full_name() or patient_user.username
        
        # Prepare context
        context = {
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'appointment': appointment,
            'queue_number': appointment.queue_number,
            'hospital_name': appointment.doctor.hospital.name if appointment.doctor.hospital else 'the clinic',
            'hospital_address': appointment.doctor.hospital.address if appointment.doctor.hospital else '',
            'appointment_details_url': settings.SITE_URL + reverse('patient_appointment_detail', args=[appointment.id]),
        }
        
        # Render HTML email
        html_content = render_to_string('emails/next_in_queue_notification.html', context)
        
        subject = f"You're Next! Time to Head to {context['hospital_name']}"
        
        # Plain text version
        text_content = f"""
Hello {patient_name},

You are next in queue! Dr. {doctor_name} is ready to see you now.

Queue Position: Q#{appointment.queue_number}
Location: {context['hospital_name']}
{f"Address: {context['hospital_address']}" if context['hospital_address'] else ""}

Please proceed to the clinic right away.

Appointment Details: {context['appointment_details_url']}

---
OkiDoki Healthcare System
support@okidoki.clinic
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"Next-in-queue notification sent to {patient_user.email} for appointment {appointment.id}"
        )
        
    except Exception as e:
        logger.error(
            f"Error sending next-in-queue email for appointment {appointment.id}: {str(e)}"
        )
        raise

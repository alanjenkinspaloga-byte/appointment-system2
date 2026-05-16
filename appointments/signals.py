# ============================================================
# appointments/signals.py — Auto-create Profile on User creation
# ============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Appointment, Doctor, Notification


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'profile'):
            role = 'admin' if instance.is_superuser else 'patient'
            Profile.objects.create(user=instance, role=role)


@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    """Fire notifications whenever an appointment is created or its status changes."""
    patient_user = instance.patient.user
    doctor_user  = instance.doctor.user
    doctor_name  = f'Dr. {doctor_user.get_full_name() or doctor_user.username}'
    patient_name = patient_user.get_full_name() or patient_user.username
    appt_date    = instance.date.strftime('%b %d, %Y')

    if created:
        Notification.objects.create(
            user=patient_user,
            notif_type='appointment_booked',
            title='Appointment Booked',
            message=f'Your appointment with {doctor_name} on {appt_date} has been received and is pending confirmation.',
        )
        Notification.objects.create(
            user=doctor_user,
            notif_type='appointment_booked',
            title='New Appointment Request',
            message=f'{patient_name} has requested an appointment on {appt_date}.',
        )
    else:
        status = instance.status
        if status == 'confirmed':
            Notification.objects.create(
                user=patient_user,
                notif_type='appointment_confirmed',
                title='Appointment Confirmed',
                message=f'Your appointment with {doctor_name} on {appt_date} has been confirmed. Queue #{instance.queue_number or "—"}.',
            )
            
            # Send confirmation email
            try:
                from .email_utils import send_online_appointment_confirmation_email, send_in_person_appointment_confirmation_email
                import logging
                email_logger = logging.getLogger(__name__)
                
                if instance.is_online_consultation and instance.jitsi_meet_link:
                    send_online_appointment_confirmation_email(instance)
                    email_logger.info(f"Online appointment confirmation email sent for appointment {instance.id}")
                else:
                    send_in_person_appointment_confirmation_email(instance)
                    email_logger.info(f"In-person appointment confirmation email sent for appointment {instance.id}")
            except Exception as e:
                import logging
                email_logger = logging.getLogger(__name__)
                email_logger.error(f"Error sending appointment confirmation email for appointment {instance.id}: {str(e)}")
            
            # Create Google Meet event if this is an online consultation
            # and doctor has Google Calendar connected
            if instance.is_online_consultation and instance.doctor.is_google_calendar_connected:
                try:
                    from .google_calendar_utils import create_google_meet_event
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    meet_link = create_google_meet_event(instance)
                    if meet_link:
                        instance.google_meet_link = meet_link
                        instance.save(update_fields=['google_meet_link'])
                        
                        # Notify both doctor and patient about the Meet link
                        Notification.objects.create(
                            user=patient_user,
                            notif_type='appointment_confirmed',
                            title='Google Meet Link Ready',
                            message=f'Your Google Meet link for the consultation is ready. The link will be sent to both your email and the doctor\'s email.',
                        )
                        logger.info(f"Google Meet event created for appointment {instance.id}: {meet_link}")
                    else:
                        logger.warning(f"Failed to create Google Meet event for appointment {instance.id}")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error creating Google Meet event for appointment {instance.id}: {str(e)}")
        elif status == 'cancelled':
            Notification.objects.create(
                user=patient_user,
                notif_type='appointment_cancelled',
                title='Appointment Cancelled',
                message=f'Your appointment with {doctor_name} on {appt_date} has been cancelled.',
            )
            Notification.objects.create(
                user=doctor_user,
                notif_type='appointment_cancelled',
                title='Appointment Cancelled',
                message=f'The appointment with {patient_name} on {appt_date} was cancelled.',
            )
        elif status == 'in_progress':
            # Notify the next patient in the queue to head to the clinic
            if instance.queue_number:
                next_appt = Appointment.objects.filter(
                    doctor=instance.doctor,
                    date=instance.date,
                    queue_number=instance.queue_number + 1,
                    status='confirmed',
                ).select_related('patient__user', 'availability__hospital').first()
                if next_appt:
                    loc = (
                        next_appt.availability.hospital.name
                        if next_appt.availability.hospital
                        else (instance.doctor.hospital.name if instance.doctor.hospital else 'the clinic')
                    )
                    Notification.objects.create(
                        user=next_appt.patient.user,
                        notif_type='queue_update',
                        title="You're Next in Queue!",
                        message=(
                            f'{doctor_name} is now seeing Patient #{instance.queue_number}. '
                            f'You are Queue #{next_appt.queue_number} \u2014 please proceed to {loc} now!'
                        ),
                    )
        elif status == 'done':
            Notification.objects.create(
                user=patient_user,
                notif_type='appointment_done',
                title='Appointment Completed',
                message=f'Your appointment with {doctor_name} on {appt_date} has been marked as complete.',
            )


@receiver(post_save, sender=Doctor)
def doctor_approval_notification(sender, instance, created, **kwargs):
    """Notify a doctor when their account is approved or revoked."""
    if created:
        return
    if instance.is_approved and instance.approved_at:
        # Only create once — use get_or_create keyed on type+user
        exists = Notification.objects.filter(
            user=instance.user,
            notif_type='doctor_approved',
        ).exists()
        if not exists:
            Notification.objects.create(
                user=instance.user,
                notif_type='doctor_approved',
                title='Account Approved',
                message='Congratulations! Your doctor account has been approved. You can now manage your schedule and accept appointments.',
            )
    elif not instance.is_approved and not instance.approved_at:
        # Revoked (was approved, now is_approved=False and approved_at cleared)
        Notification.objects.create(
            user=instance.user,
            notif_type='doctor_revoked',
            title='Account Approval Revoked',
            message='Your doctor account approval has been revoked by the admin. Please contact support if you believe this is an error.',
        )


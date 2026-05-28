# ============================================================
# appointments/signals.py — Auto-create Profile on User creation
# ============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Profile, Appointment, Doctor, Notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'profile'):
            role = 'admin' if instance.is_superuser else 'patient'
            Profile.objects.create(user=instance, role=role)


@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    """
    Fire notifications whenever an appointment is created or its status changes.
    Also schedules Celery tasks for timed email reminders.
    """
    from .tasks import send_appointment_reminder, send_next_in_queue_notification
    
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
                
                if instance.is_online_consultation and instance.jitsi_meet_link:
                    send_online_appointment_confirmation_email(instance)
                    logger.info(f"Online appointment confirmation email sent for appointment {instance.id}")
                else:
                    send_in_person_appointment_confirmation_email(instance)
                    logger.info(f"In-person appointment confirmation email sent for appointment {instance.id}")
            except Exception as e:
                logger.error(f"Error sending appointment confirmation email for appointment {instance.id}: {str(e)}")
            
            # ============================================================
            # SCHEDULE REMINDER EMAIL TASK
            # ============================================================
            try:
                reminder_datetime = instance.get_reminder_datetime()
                
                if reminder_datetime:
                    now = timezone.now()
                    
                    if reminder_datetime > now:
                        # Calculate countdown in seconds (how long to wait before running task)
                        countdown = int((reminder_datetime - now).total_seconds())
                        
                        # Schedule the reminder task with apply_async
                        task = send_appointment_reminder.apply_async(
                            args=[instance.id],
                            countdown=countdown,  # Run at specific time
                            retry=True,
                            retry_policy={
                                'max_retries': 3,
                                'interval_start': 60,  # 1 minute
                                'interval_step': 60,   # 1 minute
                                'interval_max': 300,   # 5 minutes
                            }
                        )
                        
                        # Store task ID for tracking
                        instance.scheduled_task_id = task.id
                        instance.save(update_fields=['scheduled_task_id'])
                        
                        logger.info(
                            f"Scheduled reminder task {task.id} for appointment {instance.id} "
                            f"at {reminder_datetime} (in {countdown} seconds)"
                        )
                    else:
                        logger.warning(
                            f"Reminder time {reminder_datetime} is in the past. "
                            f"Skipping task scheduling for appointment {instance.id}"
                        )
                else:
                    logger.warning(
                        f"Could not calculate reminder datetime for appointment {instance.id}. "
                        f"Skipping task scheduling."
                    )
            except Exception as e:
                logger.error(
                    f"Error scheduling reminder task for appointment {instance.id}: {str(e)}"
                )
                
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
            
            # ============================================================
            # CANCEL SCHEDULED REMINDER TASK
            # ============================================================
            try:
                if instance.scheduled_task_id:
                    from celery import current_app
                    current_app.control.revoke(instance.scheduled_task_id, terminate=True)
                    logger.info(f"Cancelled scheduled task {instance.scheduled_task_id} for appointment {instance.id}")
            except Exception as e:
                logger.error(f"Error cancelling scheduled task for appointment {instance.id}: {str(e)}")
                
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
                    
                    # ============================================================
                    # SCHEDULE "NEXT IN QUEUE" NOTIFICATION EMAIL
                    # ============================================================
                    try:
                        task = send_next_in_queue_notification.apply_async(
                            args=[next_appt.id],
                            countdown=0,  # Send immediately
                            retry=True,
                            retry_policy={
                                'max_retries': 3,
                                'interval_start': 60,
                                'interval_step': 60,
                                'interval_max': 300,
                            }
                        )
                        logger.info(
                            f"Scheduled next-in-queue notification task {task.id} "
                            f"for appointment {next_appt.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error scheduling next-in-queue notification for appointment {next_appt.id}: {str(e)}"
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


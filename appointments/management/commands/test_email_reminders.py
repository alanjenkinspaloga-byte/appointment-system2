# ============================================================
# appointments/management/commands/test_email_reminders.py
# Management Command to Test Email Reminder System
# ============================================================
"""
Django management command to test the Celery task scheduler and email reminders.

Usage:
    python manage.py test_email_reminders --help
    python manage.py test_email_reminders --simulate
    python manage.py test_email_reminders --appointment-id 5
    python manage.py test_email_reminders --queue
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from appointments.models import Appointment, Doctor, Patient, Availability, Hospital
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email reminders and Celery task scheduling for appointments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Create test appointments and simulate reminder sending',
        )
        parser.add_argument(
            '--appointment-id',
            type=int,
            help='Send reminder for specific appointment ID',
        )
        parser.add_argument(
            '--queue',
            action='store_true',
            help='Test next-in-queue notification',
        )
        parser.add_argument(
            '--check-pending',
            action='store_true',
            help='Check all pending reminder tasks',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Reminder interval in minutes (default: 30)',
        )

    def handle(self, *args, **options):
        if options['simulate']:
            self.create_test_appointments(options.get('interval', 30))
        elif options['appointment_id']:
            self.test_single_reminder(options['appointment_id'])
        elif options['queue']:
            self.test_queue_notification()
        elif options['check_pending']:
            self.check_pending_reminders()
        else:
            self.print_help()

    def print_help(self):
        """Print help information"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Email Reminder System — Test Command'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        self.stdout.write(self.style.WARNING('Usage:\n'))
        self.stdout.write('  python manage.py test_email_reminders [OPTIONS]\n')
        
        self.stdout.write(self.style.WARNING('Options:\n'))
        self.stdout.write('  --simulate              Create test appointments and schedule reminders')
        self.stdout.write('  --appointment-id ID     Send reminder for specific appointment')
        self.stdout.write('  --queue                 Test next-in-queue notification')
        self.stdout.write('  --check-pending         Show all pending reminder tasks')
        self.stdout.write('  --interval MINUTES      Reminder interval in minutes (default: 30)\n')
        
        self.stdout.write(self.style.WARNING('Examples:\n'))
        self.stdout.write('  # Create test appointments with 30-minute reminder')
        self.stdout.write('  python manage.py test_email_reminders --simulate\n')
        
        self.stdout.write('  # Create test with 2-hour reminder')
        self.stdout.write('  python manage.py test_email_reminders --simulate --interval 120\n')
        
        self.stdout.write('  # Send reminder for specific appointment')
        self.stdout.write('  python manage.py test_email_reminders --appointment-id 5\n')
        
        self.stdout.write('  # Check pending tasks')
        self.stdout.write('  python manage.py test_email_reminders --check-pending\n')

    def create_test_appointments(self, interval_minutes):
        """Create test appointments and schedule reminders"""
        self.stdout.write(self.style.SUCCESS('\n🧪 Creating test appointments...\n'))
        
        try:
            # Get or create test doctor
            doctor_user, _ = User.objects.get_or_create(
                username='test_doctor',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'Doctor',
                    'email': 'doctor@test.local',
                }
            )
            
            doctor, _ = Doctor.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'specialization': 'Pediatrics',
                    'consultation_fee': 500,
                    'is_approved': True,
                }
            )
            
            # Get or create test patient
            patient_user, _ = User.objects.get_or_create(
                username='test_patient',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'Patient',
                    'email': 'patient@test.local',
                }
            )
            
            patient, _ = Patient.objects.get_or_create(user=patient_user)
            
            # Get or create hospital
            hospital, _ = Hospital.objects.get_or_create(
                name='Test Hospital',
                defaults={'address': '123 Test St'}
            )
            
            doctor.hospital = hospital
            doctor.save()
            
            # Create availability (2 hours from now)
            tomorrow = timezone.now().date() + timedelta(days=1)
            availability, _ = Availability.objects.get_or_create(
                doctor=doctor,
                date=tomorrow,
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timedelta(hours=8)).time(),
                defaults={
                    'hospital': hospital,
                    'is_available': True,
                    'max_patients': 20,
                }
            )
            
            # Create appointment (reminder time in the future)
            appt_datetime = timezone.now() + timedelta(minutes=interval_minutes + 5)
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                availability=availability,
                date=appt_datetime.date(),
                appointment_time=appt_datetime.time(),
                status='pending',
                reminder_interval_minutes=interval_minutes,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created test appointment #{appointment.id}')
            )
            self.stdout.write(f'  Patient: {patient_user.email}')
            self.stdout.write(f'  Doctor: {doctor_user.email}')
            self.stdout.write(f'  Appointment time: {appt_datetime.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write(f'  Reminder interval: {interval_minutes} minutes')
            
            # Confirm the appointment to trigger reminder scheduling
            appointment.status = 'confirmed'
            appointment.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Appointment confirmed - reminder should be scheduled')
            )
            self.stdout.write(f'  Scheduled task ID: {appointment.scheduled_task_id}')
            self.stdout.write(f'  Reminder time: {appointment.get_reminder_datetime().strftime("%Y-%m-%d %H:%M")}')
            
            self.stdout.write(
                self.style.WARNING(
                    f'\n💡 Reminder email will be sent in {interval_minutes} minutes\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to create test appointments: {str(e)}')

    def test_single_reminder(self, appointment_id):
        """Test sending reminder for a specific appointment"""
        self.stdout.write(f'\n🧪 Testing reminder for appointment #{appointment_id}...\n')
        
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            self.stdout.write(f'Patient: {appointment.patient.user.email}')
            self.stdout.write(f'Doctor: Dr. {appointment.doctor.user.get_full_name()}')
            self.stdout.write(f'Appointment: {appointment.date} {appointment.appointment_time}')
            self.stdout.write(f'Reminder interval: {appointment.reminder_interval_minutes} minutes')
            
            # Send the reminder
            from appointments.tasks import send_appointment_reminder
            result = send_appointment_reminder(appointment_id)
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Reminder sent'))
            self.stdout.write(f'  Status: {result.get("status")}')
            self.stdout.write(f'  Timestamp: {timezone.now().isoformat()}\n')
            
        except Appointment.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ Appointment #{appointment_id} not found\n')
            )
            raise CommandError(f'Appointment #{appointment_id} not found')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to send reminder: {str(e)}')

    def test_queue_notification(self):
        """Test next-in-queue notification"""
        self.stdout.write('\n🧪 Testing next-in-queue notification...\n')
        
        try:
            # Find an appointment with queue_number >= 2
            appointment = Appointment.objects.filter(
                status='confirmed',
                queue_number__gte=2
            ).select_related(
                'patient__user', 'doctor__user'
            ).first()
            
            if not appointment:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠ No suitable appointment found for testing.\n'
                        'You need confirmed appointments in queue.\n'
                    )
                )
                return
            
            self.stdout.write(f'Testing with appointment #{appointment.id}')
            self.stdout.write(f'Patient: {appointment.patient.user.email}')
            self.stdout.write(f'Queue #: {appointment.queue_number}')
            
            # Send the notification
            from appointments.tasks import send_next_in_queue_notification
            result = send_next_in_queue_notification(appointment.id)
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Next-in-queue notification sent'))
            self.stdout.write(f'  Status: {result.get("status")}')
            self.stdout.write(f'  Timestamp: {timezone.now().isoformat()}\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to send notification: {str(e)}')

    def check_pending_reminders(self):
        """Show all pending reminder tasks"""
        self.stdout.write('\n📋 Checking pending reminders...\n')
        
        try:
            now = timezone.now()
            
            # Find appointments due for reminders
            pending = Appointment.objects.filter(
                status__in=['confirmed', 'pending'],
                reminder_sent_at__isnull=True,
            ).select_related(
                'patient__user', 'doctor__user'
            ).order_by('date', 'appointment_time')
            
            if not pending.exists():
                self.stdout.write(self.style.SUCCESS('✓ No pending reminders\n'))
                return
            
            self.stdout.write(
                self.style.WARNING(f'Found {pending.count()} pending reminder(s):\n')
            )
            
            for i, appt in enumerate(pending[:10], 1):
                reminder_time = appt.get_reminder_datetime()
                status = '⏰ Due now' if reminder_time <= now else '⏳ Pending'
                time_until = reminder_time - now if reminder_time else None
                
                self.stdout.write(f'{i}. Appointment #{appt.id} - {status}')
                self.stdout.write(f'   Patient: {appt.patient.user.email}')
                self.stdout.write(f'   Appointment: {appt.date} {appt.appointment_time}')
                self.stdout.write(f'   Reminder: {reminder_time.strftime("%Y-%m-%d %H:%M")}')
                if time_until:
                    self.stdout.write(f'   Time until: {str(time_until).split(".")[0]}')
                self.stdout.write('')
            
            if pending.count() > 10:
                self.stdout.write(
                    self.style.WARNING(f'... and {pending.count() - 10} more\n')
                )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to check reminders: {str(e)}')

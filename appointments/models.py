# ============================================================
# appointments/models.py — Database Models
# ============================================================
# Models:
#   1. Profile         — Extends Django User (role: Doctor/Patient/Admin)
#   2. Hospital        — Hospital / Clinic with location (lat/lng)
#   3. Specialization  — Medical specialization categories
#   4. Symptom         — Symptoms linked to specializations
#   5. Doctor          — Doctor-specific data (Pediatrics / OB-GYN)
#   6. Patient         — Patient-specific data
#   7. Availability    — Doctor schedule slots
#   8. Appointment     — Booking between patient & doctor
#   9. Payment         — Payment record with reference number
# ============================================================

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def _safe_full_name(user):
    """Return a safe display name for a User-like object."""
    if not user:
        return None

    try:
        full_name = user.get_full_name()
    except Exception:
        full_name = None

    if full_name:
        return full_name

    return getattr(user, 'username', None) or getattr(user, 'email', None)


# --------------------------------------------------
# ROLE CHOICES
# --------------------------------------------------
ROLE_CHOICES = (
    ('doctor', 'Doctor'),
    ('patient', 'Patient'),
    ('admin', 'Admin'),
)

# --------------------------------------------------
# SPECIALIZATION CHOICES
# --------------------------------------------------
SPECIALIZATION_CHOICES = (
    ('Pediatrics', 'Pediatrics'),
    ('Obstetrics and Gynecology', 'Obstetrics and Gynecology'),
    ('Dentistry', 'Dentistry'),
)

# --------------------------------------------------
# APPOINTMENT STATUS CHOICES
# Pending → Confirmed → In Progress → Done | Cancelled
# --------------------------------------------------
APPOINTMENT_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
    ('cancelled', 'Cancelled'),
)

# --------------------------------------------------
# PAYMENT STATUS CHOICES
# --------------------------------------------------
PAYMENT_STATUS = (
    ('unpaid', 'Unpaid'),
    ('paid', 'Paid'),
)


# ============================================================
# 1. PROFILE MODEL — Extends the Django User
# ============================================================
class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = _safe_full_name(self.user) or getattr(self.user, 'username', None) or 'User'
        return f"{name} ({self.get_role_display()})"

    class Meta:
        ordering = ['-created_at']


# ============================================================
# 2. HOSPITAL MODEL — Clinics with map coordinates
# ============================================================
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=12, decimal_places=7, blank=True, null=True,
        help_text='GPS latitude (e.g. 13.4115)',
    )
    longitude = models.DecimalField(
        max_digits=12, decimal_places=7, blank=True, null=True,
        help_text='GPS longitude (e.g. 121.1804)',
    )
    phone = models.CharField(max_length=30, blank=True, null=True)
    map_embed_url = models.URLField(
        blank=True, null=True,
        help_text='Google Maps embed src URL (from Share → Embed a map → copy the src value only)',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.city or self.address[:40]}"

    class Meta:
        ordering = ['name']


# ============================================================
# 3. SPECIALIZATION MODEL
# ============================================================
class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# ============================================================
# 4. SYMPTOM MODEL
# ============================================================
class Symptom(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    specializations = models.ManyToManyField(
        Specialization, related_name='symptoms',
    )

    def __str__(self):
        specs = ', '.join(s.name for s in self.specializations.all()[:3])
        return f"{self.name} → {specs}"

    class Meta:
        ordering = ['name']


# ============================================================
# 5. DOCTOR MODEL
# ============================================================
class Doctor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='doctor_profile',
    )
    specialization = models.CharField(
        max_length=100, choices=SPECIALIZATION_CHOICES, default='Pediatrics',
    )
    specialization_category = models.ForeignKey(
        Specialization, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='doctors',
    )
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='doctors',
    )
    license_number = models.CharField(max_length=50, blank=True, null=True)
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=500.00,
    )
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)

    # --- Professional Background ---
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    medical_school = models.CharField(max_length=200, blank=True, null=True)
    year_graduated = models.PositiveIntegerField(blank=True, null=True)

    # --- Document Uploads ---
    license_certificate = models.FileField(
        upload_to='doctor_docs/license/', blank=True, null=True,
        help_text='Medical License Certificate (PDF, JPG, PNG).',
    )
    professional_id_doc = models.FileField(
        upload_to='doctor_docs/professional_id/', blank=True, null=True,
        help_text='Professional ID (PDF, JPG, PNG).',
    )
    board_certification = models.FileField(
        upload_to='doctor_docs/board_cert/', blank=True, null=True,
        help_text='Board Certification (PDF, JPG, PNG).',
    )
    government_id_doc = models.FileField(
        upload_to='doctor_docs/government_id/', blank=True, null=True,
        help_text='Government ID (PDF, JPG, PNG).',
    )

    # --- Online Presence ---
    linkedin_url = models.URLField(
        blank=True, null=True,
        help_text='LinkedIn profile URL (e.g. https://www.linkedin.com/in/yourname)',
    )
    profile_picture = models.ImageField(
        upload_to='doctor_profiles/',
        blank=True, null=True,
        help_text='Professional profile picture for credibility and recognition',
    )

    # --- Online Consultation Settings ---
    accepts_online_consultations = models.BooleanField(
        default=True,
        help_text='Whether the doctor accepts online video consultations via Jitsi Meet',
    )

    def __str__(self):
        tag = "Approved" if self.is_approved else "Pending"
        name = _safe_full_name(self.user) or getattr(self.user, 'username', None) or 'Doctor'
        return f"Dr. {name} — {self.specialization} [{tag}]"

    class Meta:
        ordering = ['user__last_name']


# ============================================================
# 6. PATIENT MODEL
# ============================================================
class Patient(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='patient_profile',
    )
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female'), ('other', 'Other')),
        blank=True, null=True,
    )
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        name = _safe_full_name(self.user) or getattr(self.user, 'username', None) or 'Patient'
        return f"Patient: {name}"

    class Meta:
        ordering = ['user__last_name']


# ============================================================
# 7. AVAILABILITY MODEL — Doctor Schedule Slots
# ============================================================
AVAILABILITY_STATUS_CHOICES = (
    ('accepting', 'Accepting Patients'),
    ('paused', 'Paused'),
)


class Availability(models.Model):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name='availabilities',
    )
    # Location for this specific schedule slot (supports multi-location doctors)
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='availabilities',
        help_text='Location for this slot (leave blank to inherit doctor\'s primary clinic).',
    )
    # Optional manual location name (for custom clinic entry)
    location_name = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Enter a custom clinic/location name if not selecting from the dropdown above.',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.PositiveIntegerField(default=20)
    # Grab-like pause/accept toggle — doctor controls this per slot
    accepting_status = models.CharField(
        max_length=10, choices=AVAILABILITY_STATUS_CHOICES, default='accepting',
        help_text='Pause to temporarily stop accepting patients at this location.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def booked_count(self):
        return self.appointments.exclude(status='cancelled').count()

    @property
    def is_fully_booked(self):
        return self.booked_count >= self.max_patients

    @property
    def effective_hospital(self):
        """Returns slot's custom location, hospital name, or falls back to doctor's primary clinic."""
        if self.location_name:
            return self.location_name
        if self.hospital:
            return self.hospital
        return self.doctor.hospital

    @property
    def is_paused(self):
        return self.accepting_status == 'paused'

    def __str__(self):
        if self.location_name:
            loc = self.location_name
        elif self.hospital:
            loc = self.hospital.name
        else:
            loc = self.doctor.hospital.name if self.doctor and self.doctor.hospital else 'Primary'

        doctor_name = _safe_full_name(getattr(self.doctor, 'user', None))
        if not doctor_name:
            doctor_name = f'Doctor#{getattr(self.doctor, "id", "—")}'

        return (
            f"Dr. {doctor_name} | "
            f"{self.date} {self.start_time}–{self.end_time} @ {loc}"
        )

    class Meta:
        verbose_name_plural = 'Availabilities'
        ordering = ['date', 'start_time']
        unique_together = ('doctor', 'hospital', 'date', 'start_time', 'end_time')


# ============================================================
# 8. APPOINTMENT MODEL
# ============================================================
class Appointment(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='appointments',
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name='appointments',
    )
    availability = models.ForeignKey(
        Availability, on_delete=models.CASCADE, related_name='appointments',
    )
    date = models.DateField()
    appointment_time = models.TimeField(
        blank=True, null=True,
        help_text='Specific time slot for the appointment (minute-by-minute)'
    )
    status = models.CharField(
        max_length=15, choices=APPOINTMENT_STATUS, default='pending',
    )
    queue_number = models.PositiveIntegerField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS, default='unpaid',
    )

    # --- Online Consultation Settings ---
    is_online_consultation = models.BooleanField(
        default=False,
        help_text='Whether this is an online consultation via Jitsi Meet',
    )
    
    # --- Jitsi Meet Integration ---
    jitsi_meet_link = models.URLField(
        blank=True, null=True,
        help_text='Jitsi Meet link for the online video consultation',
    )

    # ============================================================
    # EMAIL REMINDER & NOTIFICATION SCHEDULING
    # ============================================================
    # Reminder interval before appointment (in minutes)
    # Examples: 30 (30 min), 1440 (24 hours), 2880 (48 hours)
    reminder_interval_minutes = models.PositiveIntegerField(
        default=30,
        help_text='Minutes before appointment to send reminder email (default: 30 min)',
    )
    
    # Track if reminder email has been sent
    reminder_sent_at = models.DateTimeField(
        blank=True, null=True,
        help_text='Timestamp when reminder email was sent',
    )
    
    # Celery task ID for the scheduled reminder
    scheduled_task_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='Celery task ID for the scheduled reminder task',
    )
    
    # Track if "next in queue" notification was sent
    next_in_queue_notification_sent = models.BooleanField(
        default=False,
        help_text='Whether "you are next in queue" email has been sent',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_appointment_datetime(self):
        """
        Combine appointment date and time into a datetime object.
        Returns timezone-aware datetime in the configured timezone.
        """
        from datetime import datetime
        from django.utils import timezone
        
        if self.appointment_time:
            naive_dt = datetime.combine(self.date, self.appointment_time)
            # Make it timezone-aware (Asia/Manila)
            return timezone.make_aware(naive_dt)
        return None

    def get_reminder_datetime(self):
        """
        Calculate when the reminder email should be sent.
        This is: appointment_datetime - reminder_interval_minutes
        """
        from datetime import timedelta
        from django.utils import timezone
        
        appt_datetime = self.get_appointment_datetime()
        if appt_datetime:
            return appt_datetime - timedelta(minutes=self.reminder_interval_minutes)
        return None

    def save(self, *args, **kwargs):
        # Auto-generate queue number when confirmed
        # Queue numbers are doctor-specific and ordered by appointment time
        if self.status == 'confirmed' and self.queue_number is None:
            # Get all confirmed appointments for this doctor on this date,
            # ordered by appointment_time (specific time slot)
            confirmed_for_day = Appointment.objects.filter(
                doctor=self.doctor, 
                date=self.date,
                status='confirmed',
                queue_number__isnull=False,
            ).order_by('appointment_time')
            
            # Count appointments before this one's time
            if self.appointment_time:
                appointments_before = confirmed_for_day.filter(
                    appointment_time__lt=self.appointment_time
                ).count()
                self.queue_number = appointments_before + 1
            else:
                # Fallback: just get the next number
                last = confirmed_for_day.last()
                self.queue_number = (last.queue_number + 1) if last else 1
        super().save(*args, **kwargs)

    def get_patient_appointment_number(self):
        """Get this appointment's ordinal number for the patient (1st, 2nd, 3rd, etc.)"""
        patient_appointments = Appointment.objects.filter(
            patient=self.patient
        ).order_by('id')
        
        for index, appt in enumerate(patient_appointments, start=1):
            if appt.id == self.id:
                return index
        return 1
    
    def get_doctor_appointment_number(self):
        """Get this appointment's ordinal number for the doctor (1st, 2nd, 3rd, etc.)"""
        doctor_appointments = Appointment.objects.filter(
            doctor=self.doctor
        ).order_by('id')
        
        for index, appt in enumerate(doctor_appointments, start=1):
            if appt.id == self.id:
                return index
        return 1

    def __str__(self):
        patient_user = getattr(self.patient, 'user', None)
        doctor_user = getattr(self.doctor, 'user', None)

        patient_name = _safe_full_name(patient_user) or getattr(patient_user, 'username', None)
        if not patient_name:
            patient_name = f"Patient#{self.patient_id or '—'}"

        doctor_name = _safe_full_name(doctor_user) or getattr(doctor_user, 'username', None)
        if not doctor_name:
            doctor_name = f"Doctor#{self.doctor_id or '—'}"

        return (
            f"#{self.pk} | {patient_name} → Dr. {doctor_name} | "
            f"{self.date} Q#{self.queue_number or '—'} | {self.get_status_display()}"
        )

    class Meta:
        ordering = ['date', 'appointment_time']
        unique_together = ('doctor', 'date', 'appointment_time')


# ============================================================
# 9. PAYMENT MODEL (with reference number)
# ============================================================
class Payment(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='payment',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS, default='unpaid',
    )
    reference_number = models.CharField(
        max_length=20, unique=True, blank=True,
    )
    date_paid = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} | ₱{self.amount} | {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']


# ============================================================
# 10. NOTIFICATION MODEL
# ============================================================
NOTIFICATION_TYPES = (
    ('appointment_booked',    'Appointment Booked'),
    ('appointment_confirmed', 'Appointment Confirmed'),
    ('appointment_cancelled', 'Appointment Cancelled'),
    ('appointment_done',      'Appointment Completed'),
    ('doctor_approved',       'Doctor Approved'),
    ('doctor_revoked',        'Doctor Approval Revoked'),
    ('payment_received',      'Payment Received'),
    ('queue_update',          'Queue Update'),
    ('general',               'General'),
)


class Notification(models.Model):
    user        = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications',
    )
    notif_type  = models.CharField(
        max_length=40, choices=NOTIFICATION_TYPES, default='general',
    )
    title       = models.CharField(max_length=200)
    message     = models.TextField()
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{'READ' if self.is_read else 'UNREAD'}] {self.user.username}: {self.title}"

    class Meta:
        ordering = ['-created_at']


# ============================================================
# 10. JITSI LINK LOG MODEL (for analytics)
# ============================================================
class JitsiLinkLog(models.Model):
    """Track Jitsi Meet link generation and usage for analytics."""
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE,
        related_name='jitsi_link_log', null=True, blank=True,
    )
    jitsi_room_name = models.CharField(
        max_length=255,
        help_text='Jitsi room name (e.g., okidoki-5-12-42-a7c3d9e2)',
    )
    jitsi_url = models.URLField(
        help_text='Full Jitsi Meet URL',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics fields
    link_accessed_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times the link has been accessed',
    )
    doctor_accessed_at = models.DateTimeField(
        blank=True, null=True,
        help_text='Timestamp when doctor first accessed the link',
    )
    patient_accessed_at = models.DateTimeField(
        blank=True, null=True,
        help_text='Timestamp when patient first accessed the link',
    )
    
    def __str__(self):
        return f"Jitsi Link: {self.jitsi_room_name} (Appt #{self.appointment.id if self.appointment else 'N/A'})"
    
    class Meta:
        ordering = ['-created_at']


# ============================================================
# 11. CONTACT MESSAGE MODEL
# ============================================================
class ContactMessage(models.Model):
    TOPIC_CHOICES = (
        ('appointment', 'Appointment Inquiry'),
        ('registration', 'Doctor Registration'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    )
    
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='other')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "READ" if self.is_read else "UNREAD"
        return f"[{status}] {self.full_name} — {self.get_topic_display()}"
    
    class Meta:
        ordering = ['-created_at']

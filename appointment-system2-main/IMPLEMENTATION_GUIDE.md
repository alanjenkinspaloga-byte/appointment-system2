# Google Calendar Integration - Implementation Guide

This guide shows how to integrate the Google Calendar system with your existing Django views.

## 1. Update Appointment Booking View

Add this to your `book_appointment` view or `BookAppointmentView`:

```python
from .models import Appointment
from .forms import AppointmentBookingForm

class BookAppointmentView(LoginRequiredMixin, View):
    template_name = 'patient/book_appointment.html'

    def post(self, request, availability_id):
        # ... existing code ...
        
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient_profile
            
            # Check if this is an online consultation
            is_online = request.POST.get('is_online_consultation', False)
            appointment.is_online_consultation = is_online == 'on'
            
            appointment.save()
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('patient_appointments')
```

## 2. Update Booking Template

Add this checkbox to `patient/book_appointment.html`:

```html
<div class="form-group">
    <div class="custom-control custom-checkbox">
        <input type="checkbox" 
               class="custom-control-input" 
               id="is_online" 
               name="is_online_consultation">
        <label class="custom-control-label" for="is_online">
            <i class="bi bi-video mr-2"></i>
            This is an online consultation (Google Meet)
        </label>
    </div>
    <small class="form-text text-muted">
        If checked, a Google Meet link will be automatically created when the doctor confirms this appointment.
    </small>
</div>
```

## 3. Update Appointment Detail View

Add this to show the Google Meet link:

```python
class PatientAppointmentDetailView(LoginRequiredMixin, View):
    template_name = 'patient/appointment_detail.html'

    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Authorization check
        if request.user.patient_profile != appointment.patient:
            messages.error(request, 'Access denied.')
            return redirect('patient_appointments')
        
        context = {
            'appointment': appointment,
            'is_online_consultation': appointment.is_online_consultation,
            'google_meet_link': appointment.google_meet_link,
            'show_meet_button': (
                appointment.is_online_consultation and 
                appointment.google_meet_link and
                appointment.status in ['confirmed', 'in_progress']
            ),
        }
        
        return render(request, self.template_name, context)
```

## 4. Update Doctor Appointment Confirmation

In your doctor's appointment confirmation/status change view:

```python
class UpdateAppointmentStatusView(LoginRequiredMixin, View):
    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Verify doctor ownership
        if request.user.doctor_profile != appointment.doctor:
            return redirect('doctor_appointments')
        
        new_status = request.POST.get('status')
        
        if new_status == 'confirmed':
            appointment.status = 'confirmed'
            appointment.save()  # This triggers the signal!
            
            # Signal handler in signals.py will automatically:
            # 1. Create Google Calendar event (if online consultation)
            # 2. Generate Google Meet link
            # 3. Save link to appointment.google_meet_link
            # 4. Send notifications
            
            messages.success(request, 'Appointment confirmed.')
        
        return redirect('doctor_appointments')
```

## 5. Update Appointment Status Form

Add to your appointment status update form:

```python
# In your forms.py
from django import forms
from .models import Appointment

class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('pending', 'Pending'),
            ('confirmed', 'Confirm'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancel'),
        ]
```

## 6. Email Template Enhancement

Add to your email notification templates:

```html
{% if appointment.is_online_consultation %}
<div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
    <h3>📹 Online Consultation via Google Meet</h3>
    <p>
        A Google Meet video conference link has been created for this appointment.
    </p>
    {% if appointment.google_meet_link %}
    <p>
        <a href="{{ appointment.google_meet_link }}" 
           style="display: inline-block; background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Join Google Meet
        </a>
    </p>
    {% endif %}
</div>
{% endif %}
```

## 7. API Error Handling

Add proper error handling in your views:

```python
def handle_google_calendar_error(request, error_msg):
    """Handle Google Calendar API errors gracefully."""
    from django.contrib import messages
    
    if '401' in str(error_msg):
        messages.error(
            request,
            'Google Calendar authentication expired. Please reconnect.'
        )
        return redirect('google_oauth_authorize')
    elif '403' in str(error_msg):
        messages.error(
            request,
            'Google Calendar permissions denied. Please reconnect.'
        )
        return redirect('google_oauth_authorize')
    else:
        messages.error(
            request,
            'Error creating Google Meet link. Please try again later.'
        )
        return redirect('doctor_appointments')
```

## 8. Admin Dashboard Enhancement

Add to `admin_panel/dashboard.html`:

```html
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Google Calendar Connected Doctors</h5>
            </div>
            <div class="card-body">
                <h2 class="text-primary">{{ doctors_with_google_calendar }}</h2>
                <small class="text-muted">
                    Out of {{ total_doctors }} total doctors
                </small>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Online Appointments This Month</h5>
            </div>
            <div class="card-body">
                <h2 class="text-info">{{ online_appointments_this_month }}</h2>
                <small class="text-muted">
                    {{ online_with_meet_links_this_month }} with Meet links
                </small>
            </div>
        </div>
    </div>
</div>
```

## 9. Context Data for Views

Add this to your doctor dashboard view:

```python
class DoctorDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        doctor = request.user.doctor_profile
        
        context = {
            'doctor': doctor,
            'google_calendar_connected': doctor.is_google_calendar_connected,
            'pending_online_appointments': Appointment.objects.filter(
                doctor=doctor,
                is_online_consultation=True,
                status='pending'
            ).count(),
            'upcoming_online_appointments': Appointment.objects.filter(
                doctor=doctor,
                is_online_consultation=True,
                status='confirmed',
                date__gte=date.today()
            ).count(),
        }
        
        return render(request, self.template_name, context)
```

## 10. Database Query Examples

Useful queries for analytics:

```python
# All online consultations
online_appointments = Appointment.objects.filter(
    is_online_consultation=True
)

# Online appointments with meet links
with_meet_links = online_appointments.filter(
    google_meet_link__isnull=False
)

# Online appointments without meet links
without_meet_links = online_appointments.filter(
    google_meet_link__isnull=True,
    status='confirmed'
)

# Doctor's online consultations
doctor_online = online_appointments.filter(
    doctor=doctor
)

# Today's online consultations
today_online = online_appointments.filter(
    date=date.today(),
    status__in=['confirmed', 'in_progress']
)
```

## 11. Logging and Monitoring

Add to your views:

```python
import logging

logger = logging.getLogger(__name__)

class BookAppointmentView(LoginRequiredMixin, View):
    def post(self, request, availability_id):
        try:
            # ... booking logic ...
            
            if appointment.is_online_consultation:
                logger.info(
                    f'Online appointment created: {appointment.id} '
                    f'Doctor: {appointment.doctor.user.username}'
                )
        except Exception as e:
            logger.error(
                f'Error creating online appointment: {str(e)}'
            )
            raise
```

## 12. Testing

Unit test example:

```python
from django.test import TestCase
from django.utils import timezone
from .models import Appointment, Doctor, Patient
from .google_calendar_utils import create_google_meet_event

class GoogleCalendarIntegrationTest(TestCase):
    def setUp(self):
        # Create test users and records
        self.doctor = Doctor.objects.create_user(...)
        self.patient = Patient.objects.create_user(...)
    
    def test_online_appointment_creates_meet_link(self):
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            is_online_consultation=True,
            status='pending',
            date=timezone.now().date(),
        )
        
        # Simulate confirmation
        appointment.status = 'confirmed'
        appointment.save()
        
        # Check if meet link was created
        appointment.refresh_from_db()
        self.assertIsNotNone(appointment.google_meet_link)
        self.assertTrue(appointment.google_meet_link.startswith('https://'))
```

## Quick Reference

### URLs
- Connect Google Calendar: `/appointments/google-oauth/authorize/`
- OAuth Callback: `/appointments/google-oauth-callback/`
- Disconnect: `/appointments/google-calendar/disconnect/`

### Model Fields
```python
Doctor.is_google_calendar_connected  # Boolean
Doctor.google_calendar_token         # TextField (JSON)
Appointment.is_online_consultation   # Boolean
Appointment.google_meet_link         # URLField
Appointment.google_calendar_event_id # CharField
```

### Signal Handlers
- Automatic when `Appointment.status` changes to `'confirmed'`
- Checks `is_online_consultation` and `doctor.is_google_calendar_connected`
- Creates event, generates link, sends notifications

### Environment Variables
```
GOOGLE_OAUTH_CREDENTIALS_FILE=/path/to/credentials.json
```

## Deployment Checklist

- [ ] Download and place `google_oauth_credentials.json`
- [ ] Run `python manage.py migrate`
- [ ] Update redirect URIs in Google Cloud Console
- [ ] Set `ALLOWED_HOSTS` for your domain
- [ ] Enable HTTPS on production
- [ ] Configure email settings for notifications
- [ ] Test Google Calendar connection flow
- [ ] Test appointment booking with online option
- [ ] Verify Meet links are created and sent
- [ ] Monitor logs for any errors

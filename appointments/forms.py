# ============================================================
# appointments/forms.py — Django ModelForms
# ============================================================

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    Profile, Doctor, Patient, Hospital,
    Availability, Appointment, Payment,
    Specialization, Symptom,
    ROLE_CHOICES, APPOINTMENT_STATUS, PAYMENT_STATUS,
    SPECIALIZATION_CHOICES, AVAILABILITY_STATUS_CHOICES,
)


# --------------------------------------------------
# REGISTRATION FORM (Doctor, Patient — no admin self-reg)
# --------------------------------------------------
REGISTRATION_ROLES = (
    ('patient', 'Patient'),
    ('doctor', 'Doctor'),
)


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=REGISTRATION_ROLES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_role'}),
        help_text='Register as a Doctor or Patient.',
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'Email address',
        }),
    )
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'First name',
        }),
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Last name',
        }),
    )
    # Doctor-only fields shown via JS when role == doctor
    specialization = forms.ChoiceField(
        choices=SPECIALIZATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Required for doctors.',
    )
    license_number = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Medical license number',
        }),
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2', 'role',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm password',
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


# --------------------------------------------------
# LOGIN FORM
# --------------------------------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password',
    }))


# --------------------------------------------------
# PROFILE / USER FORMS
# --------------------------------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone number',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Address',
            }),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


# --------------------------------------------------
# DOCTOR PROFILE FORM
# --------------------------------------------------
class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        # hospital & consultation_fee are managed via Clinic Settings page
        fields = [
            'specialization', 'specialization_category',
            'license_number', 'profile_picture',
        ]
        widgets = {
            'specialization': forms.Select(
                attrs={'class': 'form-select'},
                choices=SPECIALIZATION_CHOICES,
            ),
            'specialization_category': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'License number',
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control', 'accept': 'image/*',
                'help_text': 'Upload a professional profile picture (JPG, PNG)',
            }),
        }


# --------------------------------------------------
# PATIENT PROFILE FORM
# --------------------------------------------------
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['date_of_birth', 'gender', 'emergency_contact']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Emergency contact',
            }),
        }


# --------------------------------------------------
# HOSPITAL FORM (Admin manages)
# --------------------------------------------------
class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['name', 'address', 'city', 'latitude', 'longitude', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Hospital / Clinic name',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Full address',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '13.4115', 'step': '0.0000001',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '121.1804', 'step': '0.0000001',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone number',
            }),
        }


# --------------------------------------------------
# AVAILABILITY FORM
# --------------------------------------------------
class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = [
            'hospital', 'date', 'start_time', 'end_time',
            'max_patients', 'is_available', 'accepting_status',
        ]
        widgets = {
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'max_patients': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '20',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'accepting_status': forms.Select(
                choices=AVAILABILITY_STATUS_CHOICES,
                attrs={'class': 'form-select'},
            ),
        }
        labels = {
            'hospital': 'Location / Clinic',
            'accepting_status': 'Accepting Status',
        }
        help_texts = {
            'hospital': 'Select the clinic/hospital for this schedule slot.',
            'accepting_status': 'Set to "Paused" when you are currently at a different location.',
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError('Start time must be before end time.')
        return cleaned_data


# --------------------------------------------------
# APPOINTMENT BOOKING FORM (Patient books)
# --------------------------------------------------
class AppointmentBookingForm(forms.ModelForm):
    appointment_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'form-control', 
            'type': 'time',
            'id': 'id_appointment_time',
        }),
        label='Select Time Slot (HH:MM)',
        help_text='Choose a specific time from the available slots below',
    )
    
    is_online_consultation = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_is_online_consultation',
        }),
        label='Book as Online Consultation (Google Meet)',
        help_text='Check this if you prefer a virtual appointment via Google Meet instead of visiting the clinic',
    )
    
    class Meta:
        model = Appointment
        fields = ['appointment_time', 'is_online_consultation', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Describe the reason for your visit...',
            }),
        }


# --------------------------------------------------
# APPOINTMENT STATUS UPDATE FORM (Doctor updates)
# --------------------------------------------------
class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Doctor notes...',
            }),
        }


# --------------------------------------------------
# PAYMENT FORM
# --------------------------------------------------
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0.00',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


# --------------------------------------------------
# DOCTOR CLINIC SETTINGS FORM
# --------------------------------------------------
class DoctorClinicSettingsForm(forms.Form):
    """Doctor edits their own profile + clinic/hospital details."""

    # --- Doctor fields ---
    consultation_fee = forms.DecimalField(
        max_digits=10, decimal_places=2, required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'placeholder': '500.00', 'min': '0', 'step': '0.01',
        }),
        label='Consultation Fee (₱)',
    )
    linkedin_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.linkedin.com/in/your-profile',
        }),
        label='LinkedIn Profile URL',
        help_text='Optional. Share your LinkedIn profile so patients can verify your credentials.',
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control', 'accept': 'image/*',
        }),
        label='Profile Picture',
        help_text='Upload a professional profile picture (JPG, PNG)',
    )

    # --- Clinic / Hospital fields ---
    clinic_name = forms.CharField(
        max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. Sacred Heart Clinic',
        }),
        label='Clinic / Hospital Name',
    )
    clinic_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Full street address',
        }),
        label='Address',
    )
    clinic_city = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. Calapan City',
        }),
        label='City',
    )
    clinic_phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. 0917-123-4567',
        }),
        label='Contact Number',
    )
    latitude = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. 13.3903056',
            'step': 'any', 'id': 'id_latitude',
        }),
        label='Latitude',
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. 121.1633073',
            'step': 'any', 'id': 'id_longitude',
        }),
        label='Longitude',
    )

    def clean_latitude(self):
        val = self.cleaned_data.get('latitude')
        if val is not None:
            val = round(val, 7)
            if val < -90 or val > 90:
                raise forms.ValidationError('Latitude must be between -90 and 90.')
        return val

    def clean_longitude(self):
        val = self.cleaned_data.get('longitude')
        if val is not None:
            val = round(val, 7)
            if val < -180 or val > 180:
                raise forms.ValidationError('Longitude must be between -180 and 180.')
        return val
    map_embed_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Paste Google Maps embed src URL here (optional)',
        }),
        label='Google Maps Embed URL',
        help_text='From Google Maps → Share → Embed a map → copy the src value only.',
    )


# --------------------------------------------------
# SYMPTOM / CONDITION SEARCH FORM
# --------------------------------------------------
class SymptomSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Search symptoms (e.g., fever, headache, cramps)...',
            'autofocus': True,
        }),
        label='Symptom or Condition',
    )
    city = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by city (optional)',
        }),
        label='City',
    )


# --------------------------------------------------
# DOCTOR PROFESSIONAL INFO FORM (Step 2 of doctor sign-up)
# --------------------------------------------------
_ALLOWED_DOC_EXTS = ['.pdf', '.jpg', '.jpeg', '.png']
_MAX_DOC_BYTES = 10 * 1024 * 1024  # 10 MB


def _validate_doc_file(f):
    """Validate uploaded document: extension and size."""
    if not f:
        return
    import os as _os
    ext = _os.path.splitext(f.name)[1].lower()
    if ext not in _ALLOWED_DOC_EXTS:
        raise forms.ValidationError('Only PDF, JPG, and PNG files are accepted.')
    if f.size > _MAX_DOC_BYTES:
        raise forms.ValidationError('File size must not exceed 10 MB.')


class DoctorProfessionalInfoForm(forms.ModelForm):
    """
    Second-step form filled by doctors after initial registration.
    Collects professional background and document uploads.
    All fields are required — doctors cannot skip this step.
    """

    class Meta:
        model = Doctor
        fields = [
            'specialization',
            'license_number',
            'years_of_experience',
            'medical_school',
            'year_graduated',
            'license_certificate',
            'professional_id_doc',
            'board_certification',
            'government_id_doc',
        ]
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. PRC-0123456',
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 5',
                'min': '0',
                'max': '60',
            }),
            'medical_school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. University of the Philippines College of Medicine',
            }),
            'year_graduated': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2015',
                'min': '1950',
                'max': '2030',
            }),
            'license_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'professional_id_doc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'board_certification': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'government_id_doc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field_name in self.fields:
            self.fields[field_name].required = True
        # File fields: only required when creating (no existing file)
        instance = kwargs.get('instance')
        for file_field in ['license_certificate', 'professional_id_doc', 'board_certification', 'government_id_doc']:
            if instance and getattr(instance, file_field):
                self.fields[file_field].required = False

    def clean_license_certificate(self):
        f = self.cleaned_data.get('license_certificate')
        _validate_doc_file(f)
        return f

    def clean_professional_id_doc(self):
        f = self.cleaned_data.get('professional_id_doc')
        _validate_doc_file(f)
        return f

    def clean_board_certification(self):
        f = self.cleaned_data.get('board_certification')
        _validate_doc_file(f)
        return f

    def clean_government_id_doc(self):
        f = self.cleaned_data.get('government_id_doc')
        _validate_doc_file(f)
        return f

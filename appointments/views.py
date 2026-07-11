# ============================================================
# appointments/views.py — All Views
# ============================================================
# Sections:
#   1. Authentication (Register, Login, Logout)
#   2. Dashboard (role-based redirect)
#   3. Admin views (approve doctors, hospitals, overview)
#   4. Doctor views (availability, appointments, history)
#   5. Patient views (category select, doctors, booking)
#   6. Payment views
#   7. Profile
#   8. Symptom search
#   9. Home
# ============================================================

import json
from collections import Counter
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q, Count, Min, F

from .models import (
    Profile, Doctor, Patient, Hospital,
    Availability, Appointment, Payment,
    Specialization, Symptom, Notification,
)
from .forms import (
    RegistrationForm, LoginForm,
    ProfileForm, UserUpdateForm,
    DoctorForm, PatientForm, HospitalForm,
    AvailabilityForm, AppointmentBookingForm,
    AppointmentStatusForm, PaymentForm,
    SymptomSearchForm, DoctorClinicSettingsForm,
    DoctorProfessionalInfoForm,
)
from .decorators import doctor_required, patient_required, admin_required
from .utils import translate_to_english, language_display_name


# ============================================================
# 1. AUTHENTICATION
# ============================================================

class RegisterView(View):
    template_name = 'registration/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            role = form.cleaned_data['role']
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            # Refresh the cached profile on the user object so that
            # login() won't re-save a stale copy with role='patient'
            user.refresh_from_db()
            user.profile  # re-cache

            if role == 'doctor':
                spec = form.cleaned_data.get('specialization', 'Pediatrics')
                lic = form.cleaned_data.get('license_number', '')
                # Link specialization_category FK
                spec_obj = Specialization.objects.filter(name__icontains=spec).first()
                Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'specialization': spec,
                        'license_number': lic,
                        'specialization_category': spec_obj,
                        'is_approved': False,
                    },
                )
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.info(
                    request,
                    'Account created! Please complete your professional information below.'
                )
                return redirect('doctor_professional_info')
            elif role == 'patient':
                Patient.objects.get_or_create(user=user)
                messages.success(
                    request,
                    f'Welcome, {user.first_name}! Your patient account is ready.'
                )

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')

        return render(request, self.template_name, {'form': form})


class LoginView(View):
    template_name = 'registration/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')


class DoctorProfessionalInfoView(LoginRequiredMixin, View):
    """
    Step 2 of doctor registration — professional background and document uploads.
    Doctors are redirected here immediately after creating their account.
    They can also return to update this information later.
    """
    template_name = 'registration/doctor_professional_info.html'

    def _get_doctor(self, user):
        try:
            return user.doctor_profile
        except Doctor.DoesNotExist:
            return None

    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'doctor':
            messages.error(request, 'This page is for doctors only.')
            return redirect('dashboard')
        doctor = self._get_doctor(request.user)
        if doctor is None:
            messages.error(request, 'Doctor profile not found. Please contact admin.')
            return redirect('dashboard')
        form = DoctorProfessionalInfoForm(instance=doctor)
        return render(request, self.template_name, {'form': form, 'doctor': doctor})

    def post(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'doctor':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        doctor = self._get_doctor(request.user)
        if doctor is None:
            messages.error(request, 'Doctor profile not found.')
            return redirect('dashboard')
        form = DoctorProfessionalInfoForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            doc = form.save(commit=False)
            spec_name = form.cleaned_data.get('specialization', '')
            spec_obj = Specialization.objects.filter(name__icontains=spec_name).first()
            doc.specialization_category = spec_obj
            doc.save()
            logout(request)
            messages.success(
                request,
                'Professional information saved! Your account is pending admin approval. '
                'You will receive a notification once approved.'
            )
            return redirect('login')
        return render(request, self.template_name, {'form': form, 'doctor': doctor})


# ============================================================
# 2. DASHBOARD — role-based redirect
# ============================================================

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user, role='patient')

        role = user.profile.role
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'doctor':
            return redirect('doctor_dashboard')
        elif role == 'patient':
            return redirect('patient_dashboard')

        messages.warning(request, 'Profile not found. Please contact admin.')
        return redirect('login')


# ============================================================
# 3. ADMIN VIEWS
# ============================================================

class AdminDashboardView(LoginRequiredMixin, View):
    template_name = 'admin_panel/dashboard.html'

    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')

        today = date.today()
        from .models import ContactMessage
        unread_messages = ContactMessage.objects.filter(is_read=False).count()
        
        context = {
            'total_doctors': Doctor.objects.count(),
            'pending_doctors': Doctor.objects.filter(is_approved=False).count(),
            'approved_doctors': Doctor.objects.filter(is_approved=True).count(),
            'total_patients': Patient.objects.count(),
            'total_hospitals': Hospital.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'todays_appointments': Appointment.objects.filter(date=today).count(),
            'pending_appointments': Appointment.objects.filter(status='pending').count(),
            'today': today,
            'unread_messages_count': unread_messages,
        }
        return render(request, self.template_name, context)


class AdminDoctorListView(LoginRequiredMixin, View):
    """Admin views all doctors and their approval status."""
    template_name = 'admin_panel/doctor_list.html'

    def get(self, request):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')

        status_filter = request.GET.get('status', '')
        doctors = Doctor.objects.select_related('user', 'hospital', 'specialization_category')

        if status_filter == 'pending':
            doctors = doctors.filter(is_approved=False)
        elif status_filter == 'approved':
            doctors = doctors.filter(is_approved=True)

        return render(request, self.template_name, {
            'doctors': doctors,
            'status_filter': status_filter,
        })


class AdminApproveDoctorView(LoginRequiredMixin, View):
    """Admin approves or rejects a doctor."""

    def post(self, request, doctor_id):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')

        doctor = get_object_or_404(Doctor, pk=doctor_id)
        action = request.POST.get('action', '')
        next_page = request.POST.get('next', 'admin_doctors')

        if action == 'approve':
            doctor.is_approved = True
            doctor.approved_at = timezone.now()
            doctor.save()
            messages.success(
                request,
                f'Dr. {doctor.user.get_full_name()} has been approved!'
            )
        elif action == 'reject':
            doctor.is_approved = False
            doctor.approved_at = None
            doctor.save()
            messages.warning(
                request,
                f'Dr. {doctor.user.get_full_name()} approval revoked.'
            )

        if next_page == 'admin_review_doctor':
            from django.urls import reverse
            return redirect(reverse('admin_review_doctor', args=[doctor_id]))
        return redirect('admin_doctors')


class AdminDoctorReviewView(LoginRequiredMixin, View):
    """Admin reviews a doctor's professional documents before approving."""
    template_name = 'admin_panel/doctor_review.html'

    def get(self, request, doctor_id):
        if request.user.profile.role != 'admin':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        doctor = get_object_or_404(
            Doctor.objects.select_related('user', 'hospital', 'specialization_category'),
            pk=doctor_id,
        )
        return render(request, self.template_name, {'doctor': doctor})


class AdminHospitalListView(LoginRequiredMixin, View):
    """Admin views and manages hospitals."""
    template_name = 'admin_panel/hospital_list.html'

    def get(self, request):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')

        hospitals = Hospital.objects.annotate(doctor_count=Count('doctors'))
        return render(request, self.template_name, {'hospitals': hospitals})


class AdminHospitalCreateView(LoginRequiredMixin, View):
    """Admin creates a new hospital."""
    template_name = 'admin_panel/hospital_form.html'

    def get(self, request):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')
        form = HospitalForm()
        return render(request, self.template_name, {
            'form': form, 'title': 'Add Hospital',
        })

    def post(self, request):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')
        form = HospitalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital added successfully!')
            return redirect('admin_hospitals')
        return render(request, self.template_name, {
            'form': form, 'title': 'Add Hospital',
        })


class AdminHospitalEditView(LoginRequiredMixin, View):
    """Admin edits an existing hospital."""
    template_name = 'admin_panel/hospital_form.html'

    def get(self, request, pk):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')
        hospital = get_object_or_404(Hospital, pk=pk)
        form = HospitalForm(instance=hospital)
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Hospital', 'hospital': hospital,
        })

    def post(self, request, pk):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')
        hospital = get_object_or_404(Hospital, pk=pk)
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital updated!')
            return redirect('admin_hospitals')
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Hospital', 'hospital': hospital,
        })


class AdminHospitalDeleteView(LoginRequiredMixin, View):
    """Admin deletes a hospital."""

    def post(self, request, pk):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')
        hospital = get_object_or_404(Hospital, pk=pk)
        hospital.delete()
        messages.success(request, 'Hospital deleted.')
        return redirect('admin_hospitals')


class AdminAppointmentListView(LoginRequiredMixin, View):
    """Admin views all appointments across the system."""
    template_name = 'admin_panel/appointment_list.html'

    def get(self, request):
        if request.user.profile.role != 'admin':
            return redirect('dashboard')

        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')
        appointments = Appointment.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__hospital',
        )

        if status_filter:
            appointments = appointments.filter(status=status_filter)
        if date_filter:
            appointments = appointments.filter(date=date_filter)

        return render(request, self.template_name, {
            'appointments': appointments,
            'status_filter': status_filter,
            'date_filter': date_filter,
        })


# ============================================================
# 4. DOCTOR VIEWS
# ============================================================

class DoctorClinicSettingsView(LoginRequiredMixin, View):
    """Doctor updates their consultation fee and clinic/hospital details."""
    template_name = 'doctor/settings.html'

    def _check_doctor(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'doctor':
            messages.error(request, 'Access denied.')
            return None
        try:
            return request.user.doctor_profile
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return None

    def get(self, request):
        doctor = self._check_doctor(request)
        if not doctor:
            return redirect('dashboard')

        h = doctor.hospital
        initial = {
            'consultation_fee': doctor.consultation_fee,
            'linkedin_url':     doctor.linkedin_url or '',
            'clinic_name':    h.name           if h else '',
            'clinic_address': h.address        if h else '',
            'clinic_city':    h.city           if h else '',
            'clinic_phone':   h.phone          if h else '',
            'latitude':       h.latitude       if h else None,
            'longitude':      h.longitude      if h else None,
            'map_embed_url':  h.map_embed_url  if h else '',
            'accepts_online_consultations': doctor.accepts_online_consultations,
        }
        form = DoctorClinicSettingsForm(initial=initial)
        return render(request, self.template_name, {'form': form, 'doctor': doctor})

    def post(self, request):
        doctor = self._check_doctor(request)
        if not doctor:
            return redirect('dashboard')

        form = DoctorClinicSettingsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # Update doctor fee, LinkedIn, and online consultation preference
            doctor.consultation_fee = cd['consultation_fee']
            doctor.linkedin_url = cd.get('linkedin_url') or None
            doctor.accepts_online_consultations = cd.get('accepts_online_consultations', True)
            doctor.save(update_fields=['consultation_fee', 'linkedin_url', 'accepts_online_consultations'])

            # Update or create hospital
            h = doctor.hospital
            if h:
                h.name          = cd['clinic_name']
                h.address       = cd['clinic_address']
                h.city          = cd['clinic_city']
                h.phone         = cd['clinic_phone']
                h.latitude      = cd['latitude']
                h.longitude     = cd['longitude']
                h.map_embed_url = cd['map_embed_url']
                h.save()
            else:
                h = Hospital.objects.create(
                    name          = cd['clinic_name'],
                    address       = cd['clinic_address'],
                    city          = cd['clinic_city'],
                    phone         = cd['clinic_phone'],
                    latitude      = cd['latitude'],
                    longitude     = cd['longitude'],
                    map_embed_url = cd['map_embed_url'],
                )
                doctor.hospital = h
                doctor.save(update_fields=['hospital'])

            messages.success(request, 'Clinic settings saved successfully.')
            return redirect('doctor_settings')
        else:
            messages.error(request, 'Please fix the errors below.')

        return render(request, self.template_name, {'form': form, 'doctor': doctor})


class DoctorDashboardView(LoginRequiredMixin, View):
    template_name = 'doctor/dashboard.html'

    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'doctor':
            messages.error(request, 'Access denied. Doctors only.')
            return redirect('dashboard')

        doctor, _ = Doctor.objects.get_or_create(
            user=request.user, defaults={'specialization': 'Pediatrics'}
        )
        today = date.today()

        todays_appointments = Appointment.objects.filter(
            doctor=doctor, date=today,
        ).order_by('queue_number')

        todays_walkin_appointments = todays_appointments.filter(
            is_online_consultation=False,
        )
        todays_online_appointments = todays_appointments.filter(
            is_online_consultation=True,
        )

        pending_appointments = Appointment.objects.filter(
            doctor=doctor, status='pending',
        )
        pending_walkin_appointments = pending_appointments.filter(
            is_online_consultation=False,
        )
        pending_online_appointments = pending_appointments.filter(
            is_online_consultation=True,
        )

        upcoming_availability = Availability.objects.filter(
            doctor=doctor, date__gte=today, is_available=True,
        )[:5]

        total_patients_today = todays_appointments.filter(
            status__in=['confirmed', 'in_progress', 'done']
        ).count()

        week_start = today - timedelta(days=today.weekday())
        now = timezone.localtime()
        next_24h = now + timedelta(hours=24)
        upcoming_qs = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed'],
            appointment_time__isnull=False,
        ).order_by('date', 'appointment_time')
        upcoming_24h_appointments = [
            appt for appt in upcoming_qs
            if appt.get_appointment_datetime() and now <= appt.get_appointment_datetime() <= next_24h
        ]

        week_appointments = Appointment.objects.filter(
            doctor=doctor,
            date__gte=week_start,
            date__lte=today,
        )

        completed_count = week_appointments.filter(status='done').count()
        cancelled_count = week_appointments.filter(status='cancelled').count()
        no_show_count = 0
        walkin_count = week_appointments.filter(is_online_consultation=False).count()
        online_count = week_appointments.filter(is_online_consultation=True).count()

        appointment_times = [
            appt.get_appointment_datetime()
            for appt in week_appointments
            if appt.get_appointment_datetime()
        ]
        appointment_times.sort()
        gaps = [
            int((appointment_times[i + 1] - appointment_times[i]).total_seconds() / 60)
            for i in range(len(appointment_times) - 1)
            if appointment_times[i + 1].date() == appointment_times[i].date()
        ]
        avg_gap_minutes = round(sum(gaps) / len(gaps), 1) if gaps else None
        total_idle_minutes = sum(gaps)
        peak_hours_counter = Counter(dt.hour for dt in appointment_times)
        peak_hours = [
            {'hour': hour, 'count': count}
            for hour, count in sorted(peak_hours_counter.items(), key=lambda item: (-item[1], item[0]))[:3]
        ]

        overtime_appointments = week_appointments.filter(
            appointment_time__isnull=False,
            appointment_time__gt=F('availability__end_time'),
        ).count()

        week_patient_ids = set(week_appointments.values_list('patient_id', flat=True).distinct())
        doctor_patient_appointments = Appointment.objects.filter(doctor=doctor).values(
            'patient'
        ).annotate(first_date=Min('date'))
        first_date_by_patient = {
            item['patient']: item['first_date']
            for item in doctor_patient_appointments
        }
        new_patients_count = sum(
            1 for patient_id in week_patient_ids
            if first_date_by_patient.get(patient_id) >= week_start
        )
        returning_patients_count = sum(
            1 for patient_id in week_patient_ids
            if first_date_by_patient.get(patient_id) < week_start
        )
        follow_up_rate = round(
            (returning_patients_count / len(week_patient_ids) * 100), 1
        ) if week_patient_ids else 0

        gender_distribution = {
            'male': 0,
            'female': 0,
            'other': 0,
            'unknown': 0,
        }
        for item in week_appointments.values('patient__gender').annotate(
            count=Count('patient', distinct=True)
        ):
            gender = item['patient__gender'] or 'unknown'
            gender_distribution[gender] = item['count']

        age_groups = {
            '0-17': 0,
            '18-35': 0,
            '36-55': 0,
            '56+': 0,
            'unknown': 0,
        }
        patients_in_week = Patient.objects.filter(
            appointments__doctor=doctor,
            appointments__date__gte=week_start,
            appointments__date__lte=today,
        ).distinct()
        for patient in patients_in_week:
            if patient.date_of_birth:
                age = today.year - patient.date_of_birth.year - (
                    (today.month, today.day) <
                    (patient.date_of_birth.month, patient.date_of_birth.day)
                )
                if age < 18:
                    age_groups['0-17'] += 1
                elif age <= 35:
                    age_groups['18-35'] += 1
                elif age <= 55:
                    age_groups['36-55'] += 1
                else:
                    age_groups['56+'] += 1
            else:
                age_groups['unknown'] += 1

        top_reasons = list(
            week_appointments
            .exclude(reason__isnull=True)
            .exclude(reason__exact='')
            .values('reason')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        context = {
            'doctor': doctor,
            'todays_appointments': todays_appointments,
            'todays_walkin_appointments': todays_walkin_appointments,
            'todays_online_appointments': todays_online_appointments,
            'pending_appointments': pending_appointments,
            'pending_walkin_appointments': pending_walkin_appointments,
            'pending_online_appointments': pending_online_appointments,
            'upcoming_availability': upcoming_availability,
            'total_patients_today': total_patients_today,
            'total_pending': pending_appointments.count(),
            'today': today,
            'total_appointments_today': todays_appointments.count(),
            'total_appointments_week': week_appointments.count(),
            'upcoming_24h_count': len(upcoming_24h_appointments),
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'no_show_count': no_show_count,
            'walkin_count': walkin_count,
            'online_count': online_count,
            'peak_hours': peak_hours,
            'avg_gap_minutes': avg_gap_minutes,
            'total_idle_minutes': total_idle_minutes,
            'overtime_count': overtime_appointments,
            'new_patients_count': new_patients_count,
            'returning_patients_count': returning_patients_count,
            'follow_up_rate': follow_up_rate,
            'gender_distribution': gender_distribution,
            'age_groups': age_groups,
            'top_reasons': top_reasons,
        }
        return render(request, self.template_name, context)


class AvailabilityListView(LoginRequiredMixin, View):
    template_name = 'doctor/availability_list.html'

    def get(self, request):
        doctor, _ = Doctor.objects.get_or_create(
            user=request.user, defaults={'specialization': 'Pediatrics'})
        availabilities = Availability.objects.filter(doctor=doctor)
        return render(request, self.template_name, {
            'availabilities': availabilities, 'doctor': doctor,
        })


class AvailabilityCreateView(LoginRequiredMixin, View):
    template_name = 'doctor/availability_form.html'

    def _check_approved(self, request):
        """Return the doctor if approved, or redirect with error."""
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return None, redirect('dashboard')
        if not doctor.is_approved:
            messages.warning(
                request,
                'Your account is pending admin approval. '
                'You cannot manage schedules until your profile is approved.'
            )
            return None, redirect('availability_list')
        return doctor, None

    def get(self, request):
        doctor, redir = self._check_approved(request)
        if redir:
            return redir
        form = AvailabilityForm()
        return render(request, self.template_name, {
            'form': form, 'title': 'Add Availability',
        })

    def post(self, request):
        doctor, redir = self._check_approved(request)
        if redir:
            return redir
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = doctor
            try:
                availability.save()
                messages.success(request, 'Availability slot added!')
                return redirect('availability_list')
            except IntegrityError:
                messages.error(request, 'This time slot already exists.')
        return render(request, self.template_name, {
            'form': form, 'title': 'Add Availability',
        })


class AvailabilityEditView(LoginRequiredMixin, View):
    template_name = 'doctor/availability_form.html'

    def _check_approved(self, request):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return False
        return doctor.is_approved

    def get(self, request, pk):
        if not self._check_approved(request):
            messages.warning(request, 'Your account must be approved before managing schedules.')
            return redirect('availability_list')
        availability = get_object_or_404(
            Availability, pk=pk, doctor__user=request.user
        )
        form = AvailabilityForm(instance=availability)
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Availability',
        })

    def post(self, request, pk):
        if not self._check_approved(request):
            messages.warning(request, 'Your account must be approved before managing schedules.')
            return redirect('availability_list')
        availability = get_object_or_404(
            Availability, pk=pk, doctor__user=request.user
        )
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            messages.success(request, 'Availability updated!')
            return redirect('availability_list')
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Availability',
        })


class AvailabilityDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('availability_list')
        if not doctor.is_approved:
            messages.warning(request, 'Your account must be approved before managing schedules.')
            return redirect('availability_list')
        availability = get_object_or_404(
            Availability, pk=pk, doctor__user=request.user
        )
        availability.delete()
        messages.success(request, 'Availability slot deleted.')
        return redirect('availability_list')


class DoctorAppointmentListView(LoginRequiredMixin, View):
    template_name = 'doctor/appointment_list.html'

    def get(self, request):
        doctor, _ = Doctor.objects.get_or_create(
            user=request.user, defaults={'specialization': 'Pediatrics'})

        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')
        appointments = Appointment.objects.filter(doctor=doctor)

        if status_filter:
            appointments = appointments.filter(status=status_filter)
        if date_filter:
            appointments = appointments.filter(date=date_filter)

        walkin_appointments = appointments.filter(is_online_consultation=False)
        online_appointments = appointments.filter(is_online_consultation=True)

        return render(request, self.template_name, {
            'appointments': appointments,
            'walkin_appointments': walkin_appointments,
            'online_appointments': online_appointments,
            'doctor': doctor,
            'status_filter': status_filter,
            'date_filter': date_filter,
        })


class DoctorAppointmentDetailView(LoginRequiredMixin, View):
    template_name = 'doctor/appointment_detail.html'

    def get(self, request, pk):
        appointment = get_object_or_404(
            Appointment, pk=pk, doctor__user=request.user
        )
        form = AppointmentStatusForm(instance=appointment)
        payment_form = PaymentForm()
        payment = getattr(appointment, 'payment', None)
        if payment:
            payment_form = PaymentForm(instance=payment)

        return render(request, self.template_name, {
            'appointment': appointment,
            'form': form,
            'payment_form': payment_form,
            'payment': payment,
        })

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment, pk=pk, doctor__user=request.user
        )
        form = AppointmentStatusForm(request.POST, instance=appointment)

        if form.is_valid():
            updated = form.save(commit=False)

            # Auto-generate queue number on confirmed
            # Queue numbers are doctor-specific and ordered by appointment time
            if updated.status == 'confirmed' and appointment.queue_number is None:
                # Get all confirmed appointments for this doctor on this date,
                # ordered by appointment_time (specific time slot)
                confirmed_for_day = Appointment.objects.filter(
                    doctor=appointment.doctor, 
                    date=appointment.date,
                    status='confirmed',
                    queue_number__isnull=False,
                ).order_by('appointment_time')
                
                # Count appointments before this one's time
                if updated.appointment_time:
                    appointments_before = confirmed_for_day.filter(
                        appointment_time__lt=updated.appointment_time
                    ).count()
                    updated.queue_number = appointments_before + 1
                else:
                    # Fallback: just get the next number
                    last = confirmed_for_day.last()
                    updated.queue_number = (last.queue_number + 1) if last else 1

            updated.save()

            if updated.status == 'confirmed':
                messages.success(
                    request,
                    f'Appointment confirmed! Queue #{updated.queue_number}'
                )
            else:
                messages.success(
                    request,
                    f'Status updated to: {updated.get_status_display()}'
                )
            return redirect('doctor_appointment_detail', pk=pk)

        return render(request, self.template_name, {
            'appointment': appointment, 'form': form,
        })


class DoctorHistoryView(LoginRequiredMixin, View):
    template_name = 'doctor/history.html'

    def get(self, request):
        doctor, _ = Doctor.objects.get_or_create(
            user=request.user, defaults={'specialization': 'Pediatrics'})
        completed = Appointment.objects.filter(
            doctor=doctor, status__in=['done', 'cancelled'],
        )
        return render(request, self.template_name, {
            'appointments': completed, 'doctor': doctor,
        })


class DoctorTodayPatientsView(LoginRequiredMixin, View):
    template_name = 'doctor/today_patients.html'

    def get(self, request):
        doctor, _ = Doctor.objects.get_or_create(
            user=request.user, defaults={'specialization': 'Pediatrics'})
        today = date.today()
        appointments = Appointment.objects.filter(
            doctor=doctor, date=today,
            status__in=['confirmed', 'in_progress', 'done'],
        ).order_by('queue_number')
        walkin_appointments = appointments.filter(is_online_consultation=False)
        online_appointments = appointments.filter(is_online_consultation=True)
        return render(request, self.template_name, {
            'appointments': appointments,
            'walkin_appointments': walkin_appointments,
            'online_appointments': online_appointments,
            'doctor': doctor,
            'today': today,
        })


class DoctorToggleAvailabilityStatusView(LoginRequiredMixin, View):
    """Doctor toggles a slot between 'accepting' and 'paused' (Grab-like status toggle)."""

    def post(self, request, pk):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
            return redirect('availability_list')
        if not doctor.is_approved:
            messages.warning(request, 'Your account must be approved to manage schedules.')
            return redirect('availability_list')

        availability = get_object_or_404(Availability, pk=pk, doctor=doctor)
        if availability.accepting_status == 'accepting':
            availability.accepting_status = 'paused'
            msg = (
                f'Slot on {availability.date} ({availability.start_time}\u2013{availability.end_time}) '
                f'is now PAUSED. Patients will see alternative doctors.'
            )
        else:
            availability.accepting_status = 'accepting'
            msg = (
                f'Slot on {availability.date} ({availability.start_time}\u2013{availability.end_time}) '
                f'is now ACCEPTING patients.'
            )
        availability.save(update_fields=['accepting_status'])
        messages.success(request, msg)
        return redirect(request.POST.get('next', 'availability_list'))


# ============================================================
# 5. PATIENT VIEWS
# ============================================================

class PatientDashboardView(LoginRequiredMixin, View):
    template_name = 'patient/dashboard.html'

    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'patient':
            messages.error(request, 'Access denied. Patients only.')
            return redirect('dashboard')

        patient, _ = Patient.objects.get_or_create(user=request.user)
        today = date.today()

        upcoming = Appointment.objects.filter(
            patient=patient, date__gte=today,
        ).exclude(status__in=['cancelled', 'done']).select_related(
            'doctor__user', 'doctor__hospital', 'availability',
        )

        todays = Appointment.objects.filter(
            patient=patient, date=today,
        ).select_related('doctor__user', 'availability')

        all_appointments = Appointment.objects.filter(patient=patient)

        # ---- Queue position context for today's confirmed appointments ----
        for appt in todays:
            appt.patients_ahead = None
            appt.you_are_next = False
            if appt.status == 'confirmed' and appt.queue_number:
                ahead = Appointment.objects.filter(
                    doctor=appt.doctor,
                    date=appt.date,
                    queue_number__lt=appt.queue_number,
                    status__in=['confirmed', 'in_progress'],
                ).count()
                appt.patients_ahead = ahead
                # Check if the patient directly before is currently in progress
                in_prog = Appointment.objects.filter(
                    doctor=appt.doctor,
                    date=appt.date,
                    status='in_progress',
                    queue_number=appt.queue_number - 1,
                ).exists()
                appt.you_are_next = in_prog

        context = {
            'patient': patient,
            'upcoming_appointments': upcoming,
            'todays_appointments': todays,
            'all_appointments': all_appointments,
            'today': today,
        }
        return render(request, self.template_name, context)


class CategorySelectView(View):
    """Patient picks a category: Pediatrics or OB-GYN. No login required for browsing."""
    template_name = 'patient/category_select.html'

    def get(self, request):
        return render(request, self.template_name)


class DoctorListView(View):
    """Patient views approved doctors, optionally filtered by category. No login required for browsing."""
    template_name = 'patient/doctor_list.html'

    def get(self, request):
        category = request.GET.get('category', '')
        doctors = Doctor.objects.filter(is_approved=True).select_related(
            'user', 'hospital', 'specialization_category',
        )
        if category:
            doctors = doctors.filter(specialization__icontains=category)

        # Build JSON for map
        doctors_json = json.dumps([
            {
                'name': f"Dr. {d.user.get_full_name()}",
                'specialization': d.specialization,
                'hospital_name': d.hospital.name if d.hospital else '',
                'hospital_address': d.hospital.address if d.hospital else '',
                'city': d.hospital.city if d.hospital else '',
                'lat': float(d.hospital.latitude) if d.hospital and d.hospital.latitude else None,
                'lng': float(d.hospital.longitude) if d.hospital and d.hospital.longitude else None,
                'fee': str(d.consultation_fee),
                'pk': d.pk,
                'linkedin_url': d.linkedin_url or '',
            }
            for d in doctors
        ])

        return render(request, self.template_name, {
            'doctors': doctors,
            'doctors_json': doctors_json,
            'category': category,
        })


class CategorySelectStandaloneView(View):
    """Standalone category select page for homepage visitors. No login required, no sidebar."""
    template_name = 'patient/category_select_standalone.html'

    def get(self, request):
        return render(request, self.template_name)


class DoctorListStandaloneView(View):
    """Standalone doctor list page for homepage visitors. No login required, no sidebar."""
    template_name = 'patient/doctor_list_standalone.html'

    def get(self, request):
        category = request.GET.get('category', '')
        doctors = Doctor.objects.filter(is_approved=True).select_related(
            'user', 'hospital', 'specialization_category',
        )
        if category:
            doctors = doctors.filter(specialization__icontains=category)

        # Build JSON for map
        doctors_json = json.dumps([
            {
                'name': f"Dr. {d.user.get_full_name()}",
                'specialization': d.specialization,
                'hospital_name': d.hospital.name if d.hospital else '',
                'hospital_address': d.hospital.address if d.hospital else '',
                'city': d.hospital.city if d.hospital else '',
                'lat': float(d.hospital.latitude) if d.hospital and d.hospital.latitude else None,
                'lng': float(d.hospital.longitude) if d.hospital and d.hospital.longitude else None,
                'fee': str(d.consultation_fee),
                'pk': d.pk,
                'linkedin_url': d.linkedin_url or '',
            }
            for d in doctors
        ])

        return render(request, self.template_name, {
            'doctors': doctors,
            'doctors_json': doctors_json,
            'category': category,
        })


class DoctorScheduleView(LoginRequiredMixin, View):
    """Patient views a doctor's available schedule, grouped by location."""
    template_name = 'patient/doctor_schedule.html'

    def get(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, pk=doctor_id, is_approved=True)
        today = date.today()

        availabilities = Availability.objects.filter(
            doctor=doctor, date__gte=today, is_available=True,
        ).select_related('hospital').order_by('date', 'start_time')

        for slot in availabilities:
            slot.is_fully_booked_flag = slot.is_fully_booked

        # ---- Group slots by location ----
        # Each entry: {hospital, slots, all_paused, has_accepting, alternatives, map_embed_url, hospital_json}
        location_map = {}  # keyed by hospital pk (or 0 for no-hospital slots)
        for slot in availabilities:
            hosp = slot.hospital or doctor.hospital  # effective location
            key = hosp.pk if hosp else 0
            if key not in location_map:
                location_map[key] = {
                    'hospital': hosp,
                    'slots': [],
                    'all_paused': True,
                    'has_accepting': False,
                    'alternatives': [],
                    'map_embed_url': hosp.map_embed_url if hosp else None,
                    'hospital_json': None,
                }
                if hosp and not hosp.map_embed_url and hosp.latitude and hosp.longitude:
                    location_map[key]['hospital_json'] = json.dumps({
                        'name': hosp.name,
                        'address': hosp.address,
                        'lat': float(hosp.latitude),
                        'lng': float(hosp.longitude),
                    })
            location_map[key]['slots'].append(slot)
            if slot.accepting_status == 'accepting':
                location_map[key]['all_paused'] = False
                location_map[key]['has_accepting'] = True

        # For fully-paused locations, find alternative doctors with same specialty
        for loc_data in location_map.values():
            if loc_data['all_paused'] and loc_data['hospital'] and loc_data['hospital'].city:
                city = loc_data['hospital'].city
                spec_cat = doctor.specialization_category
                alt_q = Doctor.objects.filter(
                    is_approved=True,
                ).exclude(pk=doctor.pk)
                if spec_cat:
                    alt_q = alt_q.filter(specialization_category=spec_cat)
                else:
                    alt_q = alt_q.filter(specialization__icontains=doctor.specialization)
                alternatives = alt_q.filter(
                    Q(hospital__city__icontains=city) |
                    Q(availabilities__hospital__city__icontains=city),
                    availabilities__accepting_status='accepting',
                    availabilities__is_available=True,
                    availabilities__date__gte=today,
                ).select_related('user', 'hospital').distinct()[:5]
                loc_data['alternatives'] = list(alternatives)

        locations = list(location_map.values())

        # Fallback single-location map for doctors with no slots but a hospital
        hospital_json = None
        map_embed_url = None
        if not locations and doctor.hospital:
            if doctor.hospital.map_embed_url:
                map_embed_url = doctor.hospital.map_embed_url
            elif doctor.hospital.latitude and doctor.hospital.longitude:
                hospital_json = json.dumps({
                    'name': doctor.hospital.name,
                    'address': doctor.hospital.address,
                    'lat': float(doctor.hospital.latitude),
                    'lng': float(doctor.hospital.longitude),
                })

        return render(request, self.template_name, {
            'doctor': doctor,
            'availabilities': availabilities,
            'locations': locations,
            'hospital_json': hospital_json,
            'map_embed_url': map_embed_url,
        })


class BookAppointmentView(LoginRequiredMixin, View):
    template_name = 'patient/book_appointment.html'

    def _get_available_times(self, availability):
        """
        Generate 20-minute time slots between availability start and end time.
        Returns a list of time objects.
        """
        from datetime import datetime, timedelta
        
        start_dt = datetime.combine(date.today(), availability.start_time)
        end_dt = datetime.combine(date.today(), availability.end_time)
        
        available_times = []
        current_dt = start_dt
        
        while current_dt < end_dt:
            available_times.append(current_dt.time())
            current_dt += timedelta(minutes=20)
        
        return available_times

    def _get_booked_times(self, doctor, appointment_date):
        """Get all booked times for a doctor on a specific date."""
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            status__in=['pending', 'confirmed', 'in_progress'],
            appointment_time__isnull=False,
        ).values_list('appointment_time', flat=True)
        
        return set(booked_appointments)

    def get(self, request, availability_id):
        availability = get_object_or_404(
            Availability, pk=availability_id, is_available=True,
        )

        if availability.accepting_status == 'paused':
            messages.warning(
                request,
                'This schedule slot is currently paused. The doctor is not accepting patients '
                'at this location right now. Please check other available slots or locations.'
            )
            return redirect('doctor_schedule', doctor_id=availability.doctor.pk)

        # Get available and booked times
        available_times = self._get_available_times(availability)
        booked_times = self._get_booked_times(availability.doctor, availability.date)
        
        # Calculate free slots
        free_times = [t for t in available_times if t not in booked_times]
        
        if not free_times:
            messages.warning(request, 'All time slots are fully booked for this availability.')
            return redirect('doctor_schedule', doctor_id=availability.doctor.pk)

        form = AppointmentBookingForm()
        
        return render(request, self.template_name, {
            'form': form, 
            'availability': availability,
            'available_times': free_times,
            'booked_times': sorted(list(booked_times)),
            'total_slots': len(available_times),
            'booked_count': len(booked_times),
            'free_count': len(free_times),
        })

    def post(self, request, availability_id):
        availability = get_object_or_404(
            Availability, pk=availability_id, is_available=True,
        )
        patient, _ = Patient.objects.get_or_create(user=request.user)

        if availability.accepting_status == 'paused':
            messages.warning(request, 'This slot is currently paused.')
            return redirect('doctor_schedule', doctor_id=availability.doctor.pk)

        form = AppointmentBookingForm(request.POST)
        
        if form.is_valid():
            appointment_time = form.cleaned_data.get('appointment_time')
            is_online = form.cleaned_data.get('is_online_consultation', False)
            
            # Check if doctor accepts online consultations
            if is_online and not availability.doctor.accepts_online_consultations:
                messages.error(
                    request, 
                    'This doctor does not accept online video consultations. '
                    'Please book an in-person appointment instead.'
                )
                available_times = self._get_available_times(availability)
                booked_times = self._get_booked_times(availability.doctor, availability.date)
                free_times = [t for t in available_times if t not in booked_times]
                return render(request, self.template_name, {
                    'form': form, 
                    'availability': availability,
                    'available_times': free_times,
                    'booked_times': sorted(list(booked_times)),
                    'total_slots': len(available_times),
                    'booked_count': len(booked_times),
                    'free_count': len(free_times),
                })
            
            # Check if the time slot is still available
            booked_times = self._get_booked_times(availability.doctor, availability.date)
            
            if appointment_time in booked_times:
                messages.error(
                    request, 
                    f'Time {appointment_time.strftime("%H:%M")} is already booked. '
                    'Please select another time.'
                )
                # Re-render form with available times
                available_times = self._get_available_times(availability)
                free_times = [t for t in available_times if t not in booked_times]
                return render(request, self.template_name, {
                    'form': form, 
                    'availability': availability,
                    'available_times': free_times,
                    'booked_times': sorted(list(booked_times)),
                    'total_slots': len(available_times),
                    'booked_count': len(booked_times),
                    'free_count': len(free_times),
                })
            
            # Check if appointment_time is within availability window
            available_times = self._get_available_times(availability)
            if appointment_time not in available_times:
                messages.error(
                    request,
                    'Selected time is not a valid 20-minute slot. Please choose one of the available times.'
                )
                free_times = [t for t in available_times if t not in booked_times]
                return render(request, self.template_name, {
                    'form': form, 
                    'availability': availability,
                    'available_times': free_times,
                    'booked_times': sorted(list(booked_times)),
                    'total_slots': len(available_times),
                    'booked_count': len(booked_times),
                    'free_count': len(free_times),
                })

            if not (availability.start_time <= appointment_time < availability.end_time):
                messages.error(request, 'Selected time is outside available hours.')
                free_times = [t for t in available_times if t not in booked_times]
                return render(request, self.template_name, {
                    'form': form, 
                    'availability': availability,
                    'available_times': free_times,
                    'booked_times': sorted(list(booked_times)),
                    'total_slots': len(available_times),
                    'booked_count': len(booked_times),
                    'free_count': len(free_times),
                })
            
            appt = form.save(commit=False)
            appt.patient = patient
            appt.doctor = availability.doctor
            appt.availability = availability
            appt.date = availability.date
            appt.appointment_time = appointment_time
            appt.status = 'pending'
            
            try:
                appt.save()
                
                # Generate Jitsi Meet link if this is an online consultation
                if appt.is_online_consultation:
                    from .jitsi_utils import generate_jitsi_meet_link
                    from .models import JitsiLinkLog
                    
                    link_data = generate_jitsi_meet_link(
                        doctor_id=appt.doctor.id,
                        patient_id=appt.patient.id,
                        appointment_id=appt.id
                    )
                    appt.jitsi_meet_link = link_data['url']
                    appt.save(update_fields=['jitsi_meet_link'])
                    
                    # Log the Jitsi link generation for analytics
                    JitsiLinkLog.objects.create(
                        appointment=appt,
                        jitsi_room_name=link_data['room_name'],
                        jitsi_url=link_data['url'],
                    )
                
                messages.success(
                    request,
                    f'Appointment booked with Dr. {availability.doctor.user.get_full_name()} '
                    f'on {availability.date} at {appointment_time.strftime("%H:%M")}. '
                    f'Please wait for confirmation.'
                )
                return redirect('patient_appointments')
            except IntegrityError:
                messages.error(
                    request, 
                    f'Time {appointment_time.strftime("%H:%M")} is already used. If you just booked it, '
                    'it may have been taken by another patient. Please try a different time.'
                )
                available_times = self._get_available_times(availability)
                booked_times = self._get_booked_times(availability.doctor, availability.date)
                free_times = [t for t in available_times if t not in booked_times]
                return render(request, self.template_name, {
                    'form': form, 
                    'availability': availability,
                    'available_times': free_times,
                    'booked_times': sorted(list(booked_times)),
                    'total_slots': len(available_times),
                    'booked_count': len(booked_times),
                    'free_count': len(free_times),
                })

        # Form is invalid
        available_times = self._get_available_times(availability)
        booked_times = self._get_booked_times(availability.doctor, availability.date)
        free_times = [t for t in available_times if t not in booked_times]
        
        return render(request, self.template_name, {
            'form': form, 
            'availability': availability,
            'available_times': free_times,
            'booked_times': sorted(list(booked_times)),
            'total_slots': len(available_times),
            'booked_count': len(booked_times),
            'free_count': len(free_times),
        })


class PatientAppointmentListView(LoginRequiredMixin, View):
    template_name = 'patient/appointment_list.html'

    def get(self, request):
        patient, _ = Patient.objects.get_or_create(user=request.user)
        appointments = Appointment.objects.filter(patient=patient)
        return render(request, self.template_name, {
            'appointments': appointments, 'patient': patient,
        })


class PatientAppointmentDetailView(LoginRequiredMixin, View):
    template_name = 'patient/appointment_detail.html'

    def get(self, request, pk):
        patient, _ = Patient.objects.get_or_create(user=request.user)
        appointment = get_object_or_404(Appointment, pk=pk, patient=patient)
        payment = getattr(appointment, 'payment', None)
        return render(request, self.template_name, {
            'appointment': appointment, 'payment': payment,
        })


# ============================================================
# 6. PAYMENT VIEWS
# ============================================================

class RecordPaymentView(LoginRequiredMixin, View):
    template_name = 'doctor/record_payment.html'

    def get(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment, pk=appointment_id, doctor__user=request.user,
        )
        try:
            payment = appointment.payment
            form = PaymentForm(instance=payment)
        except Payment.DoesNotExist:
            form = PaymentForm(initial={'amount': appointment.doctor.consultation_fee})

        return render(request, self.template_name, {
            'form': form, 'appointment': appointment,
        })

    def post(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment, pk=appointment_id, doctor__user=request.user,
        )
        try:
            payment = appointment.payment
            form = PaymentForm(request.POST, instance=payment)
        except Payment.DoesNotExist:
            form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.appointment = appointment
            if payment.status == 'paid' and payment.date_paid is None:
                payment.date_paid = timezone.now()
            payment.save()

            appointment.payment_status = payment.status
            appointment.save(update_fields=['payment_status'])

            messages.success(
                request,
                f'Payment recorded! Ref: {payment.reference_number}'
            )
            return redirect('doctor_appointment_detail', pk=appointment_id)

        return render(request, self.template_name, {
            'form': form, 'appointment': appointment,
        })


# ============================================================
# 7. PROFILE VIEW
# ============================================================


# ============================================================
# 7b. NOTIFICATION VIEWS
# ============================================================

class NotificationListView(LoginRequiredMixin, View):
    """Show all notifications for the logged-in user."""
    template_name = 'notifications/notification_list.html'

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        # Mark all unread as read when the page is opened
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return render(request, self.template_name, {
            'notifications': notifications,
        })


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Mark a single notification as read via POST."""
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return redirect('notifications')


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect('notifications')


class NotificationDeleteView(LoginRequiredMixin, View):
    """Delete a single notification."""
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.delete()
        return redirect('notifications')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'profile/profile.html'

    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

        role_form = None
        if request.user.profile.role == 'doctor':
            doctor, _ = Doctor.objects.get_or_create(
                user=request.user, defaults={'specialization': 'Pediatrics'})
            role_form = DoctorForm(instance=doctor)
        elif request.user.profile.role == 'patient':
            patient, _ = Patient.objects.get_or_create(user=request.user)
            role_form = PatientForm(instance=patient)

        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
            'role_form': role_form,
        })

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)

        role_form = None
        if request.user.profile.role == 'doctor':
            doctor, _ = Doctor.objects.get_or_create(
                user=request.user, defaults={'specialization': 'Pediatrics'})
            role_form = DoctorForm(request.POST, request.FILES, instance=doctor)
        elif request.user.profile.role == 'patient':
            patient, _ = Patient.objects.get_or_create(user=request.user)
            role_form = PatientForm(request.POST, instance=patient)

        forms_valid = user_form.is_valid() and profile_form.is_valid()
        if role_form:
            forms_valid = forms_valid and role_form.is_valid()

        if forms_valid:
            user_form.save()
            profile_form.save()
            if role_form:
                role_form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')

        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
            'role_form': role_form,
        })


# ============================================================
# 8. SYMPTOM SEARCH
# ============================================================

class SymptomSearchView(LoginRequiredMixin, View):
    template_name = 'patient/symptom_search.html'

    def get(self, request):
        form = SymptomSearchForm(request.GET or None)
        results = None
        matched_symptoms = []
        matched_specializations = []
        doctors = []
        query = ''
        city_filter = ''
        translated_query = None
        detected_language = None
        language_name = None

        if form.is_valid():
            query = form.cleaned_data['query'].strip()
            city_filter = form.cleaned_data.get('city', '').strip()

            english_query, detected_language = translate_to_english(query)
            language_name = language_display_name(detected_language)

            if english_query.lower() != query.lower():
                translated_query = english_query
            else:
                english_query = query

            matched_symptoms = Symptom.objects.filter(
                Q(name__icontains=english_query) |
                Q(description__icontains=english_query)
            ).prefetch_related('specializations').distinct()

            spec_ids = set()
            for sym in matched_symptoms:
                for spec in sym.specializations.all():
                    spec_ids.add(spec.pk)

            direct_specs = Specialization.objects.filter(
                Q(name__icontains=english_query) |
                Q(description__icontains=english_query)
            )
            for spec in direct_specs:
                spec_ids.add(spec.pk)

            matched_specializations = Specialization.objects.filter(pk__in=spec_ids)

            doctor_q = Q(specialization_category__in=matched_specializations)
            doctor_q |= Q(specialization__icontains=english_query)
            for spec in matched_specializations:
                doctor_q |= Q(specialization__icontains=spec.name)
            doctors = Doctor.objects.filter(
                doctor_q, is_approved=True,
            ).select_related('user', 'specialization_category', 'hospital').distinct()

            if city_filter:
                doctors = doctors.filter(hospital__city__icontains=city_filter)

            results = True

        # Map JSON
        doctors_json = json.dumps([
            {
                'name': f"Dr. {d.user.get_full_name()}",
                'specialization': d.specialization,
                'hospital_name': d.hospital.name if d.hospital else '',
                'hospital_address': d.hospital.address if d.hospital else '',
                'city': d.hospital.city if d.hospital else '',
                'lat': float(d.hospital.latitude) if d.hospital and d.hospital.latitude else None,
                'lng': float(d.hospital.longitude) if d.hospital and d.hospital.longitude else None,
                'fee': str(d.consultation_fee),
                'pk': d.pk,
            }
            for d in doctors
        ])

        return render(request, self.template_name, {
            'form': form,
            'query': query,
            'city_filter': city_filter,
            'translated_query': translated_query,
            'detected_language': detected_language,
            'language_name': language_name,
            'matched_symptoms': matched_symptoms,
            'matched_specializations': matched_specializations,
            'doctors': doctors,
            'doctors_json': doctors_json,
            'results': results,
        })


# ============================================================
# ============================================================
# 9. CONTACT MESSAGE VIEWS
# ============================================================

class ContactMessageView(View):
    def post(self, request):
        """Handle contact form submissions from the home page."""
        from .models import ContactMessage
        
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        topic = request.POST.get('topic', 'other')
        message = request.POST.get('message', '').strip()
        
        # Validate required fields
        if not all([full_name, email, message]):
            return render(request, 'home.html', {
                'error': 'Please fill in all required fields.'
            })
        
        # Create and save contact message
        try:
            contact_msg = ContactMessage(
                full_name=full_name,
                email=email,
                phone=phone,
                topic=topic,
                message=message,
            )
            contact_msg.save()
            messages.success(
                request,
                'Thank you! Your message has been received. We\'ll respond within 24 hours.'
            )
        except Exception as e:
            messages.error(request, 'An error occurred while sending your message. Please try again.')
        
        return redirect('home')


class VideoConsultationTermsView(View):
    """Display video consultation terms and privacy notice."""
    template_name = 'video_consultation_terms.html'
    
    def get(self, request):
        return render(request, self.template_name)


class AdminMessagesView(LoginRequiredMixin, View):
    """Admin views all contact messages."""
    template_name = 'admin_panel/messages.html'
    
    def get(self, request):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        
        from .models import ContactMessage
        
        filter_status = request.GET.get('status', '')
        messages_list = ContactMessage.objects.all().order_by('-created_at')
        
        if filter_status == 'unread':
            messages_list = messages_list.filter(is_read=False)
        elif filter_status == 'read':
            messages_list = messages_list.filter(is_read=True)
        
        unread_count = ContactMessage.objects.filter(is_read=False).count()
        total_count = ContactMessage.objects.count()
        
        return render(request, self.template_name, {
            'messages': messages_list,
            'filter_status': filter_status,
            'unread_count': unread_count,
            'total_count': total_count,
            'unread_messages_count': unread_count,
        })
    
    def post(self, request):
        """Mark messages as read."""
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return redirect('admin_messages')
        
        from .models import ContactMessage
        
        action = request.POST.get('action')
        message_id = request.POST.get('message_id')
        
        if action == 'mark_read':
            msg = get_object_or_404(ContactMessage, pk=message_id)
            msg.is_read = True
            msg.save()
        
        return redirect('admin_messages')


# ============================================================
# 10. HOME
# ============================================================

class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)


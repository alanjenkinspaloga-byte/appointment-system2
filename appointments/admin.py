# ============================================================
# appointments/admin.py — Django Admin Registration
# ============================================================

from django.contrib import admin
from django.contrib.auth.models import User
from .models import (
    Profile, Hospital, Specialization, Symptom,
    Doctor, Patient, Availability, Appointment, Payment,
    Notification, ContactMessage,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'latitude', 'longitude', 'phone', 'created_at')
    search_fields = ('name', 'city', 'address')
    list_filter = ('city',)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_specializations')
    search_fields = ('name', 'description')
    filter_horizontal = ('specializations',)

    def get_specializations(self, obj):
        return ', '.join(s.name for s in obj.specializations.all()[:3])
    get_specializations.short_description = 'Specializations'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'specialization', 'hospital',
        'is_approved', 'consultation_fee',
    )
    list_filter = ('is_approved', 'specialization')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'hospital__name',
    )
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, approved_at=timezone.now())
    approve_doctors.short_description = 'Approve selected doctors'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'gender', 'emergency_contact')
    list_filter = ('gender',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'max_patients', 'is_available')
    list_filter = ('is_available', 'date', 'doctor')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'date'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'doctor', 'date',
        'status', 'queue_number', 'payment_status', 'created_at',
    )
    list_filter = ('status', 'payment_status', 'date', 'doctor')
    search_fields = (
        'patient__user__first_name', 'patient__user__last_name',
        'doctor__user__first_name', 'doctor__user__last_name',
    )
    date_hierarchy = 'date'
    readonly_fields = ('queue_number',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'appointment', 'amount', 'status', 'date_paid')
    list_filter = ('status',)
    search_fields = ('reference_number',)
    readonly_fields = ('reference_number',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notif_type', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'notif_type', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'topic', 'is_read', 'created_at')
    list_filter = ('is_read', 'topic', 'created_at')
    search_fields = ('full_name', 'email', 'message')
    readonly_fields = ('created_at', 'full_name', 'email', 'phone', 'topic', 'message')
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Mark selected messages as read'

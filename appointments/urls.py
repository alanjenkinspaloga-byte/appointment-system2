# ============================================================
# appointments/urls.py — URL Routing
# ============================================================

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_oauth import cleanup_duplicate_google_oauth, debug_google_oauth_config

urlpatterns = [

    # HOME
    path('', views.HomeView.as_view(), name='home'),
    path('contact/', views.ContactMessageView.as_view(), name='contact_message'),
    path('video-consultation-terms/', views.VideoConsultationTermsView.as_view(), name='video_consultation_terms'),

    # AUTHENTICATION
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('doctor/professional-info/', views.DoctorProfessionalInfoView.as_view(), name='doctor_professional_info'),

    # PASSWORD RESET
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), name='password_reset_complete'),

    # DASHBOARD (role-based redirect)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # PROFILE
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # ---- ADMIN URLS ----
    path('admin/cleanup-google-oauth/', cleanup_duplicate_google_oauth, name='cleanup_google_oauth'),
    path('debug-oauth-config/', debug_google_oauth_config, name='debug_oauth_config'),
    path('admin-panel/dashboard/',
         views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-panel/doctors/',
         views.AdminDoctorListView.as_view(), name='admin_doctors'),
    path('admin-panel/doctors/<int:doctor_id>/approve/',
         views.AdminApproveDoctorView.as_view(), name='admin_approve_doctor'),
    path('admin-panel/doctors/<int:doctor_id>/review/',
         views.AdminDoctorReviewView.as_view(), name='admin_review_doctor'),
    path('admin-panel/hospitals/',
         views.AdminHospitalListView.as_view(), name='admin_hospitals'),
    path('admin-panel/hospitals/add/',
         views.AdminHospitalCreateView.as_view(), name='admin_hospital_create'),
    path('admin-panel/hospitals/<int:pk>/edit/',
         views.AdminHospitalEditView.as_view(), name='admin_hospital_edit'),
    path('admin-panel/hospitals/<int:pk>/delete/',
         views.AdminHospitalDeleteView.as_view(), name='admin_hospital_delete'),
    path('admin-panel/appointments/',
         views.AdminAppointmentListView.as_view(), name='admin_appointments'),
    path('admin-panel/messages/',
         views.AdminMessagesView.as_view(), name='admin_messages'),

    # ---- DOCTOR URLS ----
    path('doctor/dashboard/',
         views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctor/settings/',
         views.DoctorClinicSettingsView.as_view(), name='doctor_settings'),
    path('doctor/availability/',
         views.AvailabilityListView.as_view(), name='availability_list'),
    path('doctor/availability/add/',
         views.AvailabilityCreateView.as_view(), name='availability_create'),
    path('doctor/availability/<int:pk>/edit/',
         views.AvailabilityEditView.as_view(), name='availability_edit'),
    path('doctor/availability/<int:pk>/delete/',
         views.AvailabilityDeleteView.as_view(), name='availability_delete'),
    path('doctor/availability/<int:pk>/toggle-status/',
         views.DoctorToggleAvailabilityStatusView.as_view(), name='availability_toggle_status'),
    path('doctor/appointments/',
         views.DoctorAppointmentListView.as_view(), name='doctor_appointments'),
    path('doctor/appointments/<int:pk>/',
         views.DoctorAppointmentDetailView.as_view(), name='doctor_appointment_detail'),
    path('doctor/history/',
         views.DoctorHistoryView.as_view(), name='doctor_history'),
    path('doctor/today-patients/',
         views.DoctorTodayPatientsView.as_view(), name='doctor_today_patients'),
    path('doctor/payment/<int:appointment_id>/',
         views.RecordPaymentView.as_view(), name='record_payment'),

    # ---- PATIENT URLS ----
    path('patient/dashboard/',
         views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('patient/categories/',
         views.CategorySelectView.as_view(), name='category_select'),
    path('patient/doctors/',
         views.DoctorListView.as_view(), name='doctor_list'),

    # ---- STANDALONE DOCTOR BROWSING (for homepage links) ----
    path('browse/categories/',
         views.CategorySelectStandaloneView.as_view(), name='category_select_standalone'),
    path('browse/doctors/',
         views.DoctorListStandaloneView.as_view(), name='doctor_list_standalone'),

    path('patient/doctors/<int:doctor_id>/schedule/',
         views.DoctorScheduleView.as_view(), name='doctor_schedule'),
    path('patient/book/<int:availability_id>/',
         views.BookAppointmentView.as_view(), name='book_appointment'),
    path('patient/appointments/',
         views.PatientAppointmentListView.as_view(), name='patient_appointments'),
    path('patient/appointments/<int:pk>/',
         views.PatientAppointmentDetailView.as_view(), name='patient_appointment_detail'),

    # SYMPTOM SEARCH
    path('patient/symptom-search/',
         views.SymptomSearchView.as_view(), name='symptom_search'),

    # NOTIFICATIONS
    path('notifications/',
         views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/mark-read/',
         views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/',
         views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('notifications/<int:pk>/delete/',
         views.NotificationDeleteView.as_view(), name='notification_delete'),
]

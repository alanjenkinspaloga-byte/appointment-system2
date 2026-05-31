# ============================================================
# clinic_project/urls.py — Root URL Configuration
# ============================================================
# All routes are delegated to the 'appointments' app.
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from appointments.views import health_check

urlpatterns = [
    # Health check endpoint for Render deployment monitoring
    path('health/', health_check, name='health_check'),

    # Django admin panel
    path('admin/', admin.site.urls),

    # Django-allauth routes (Google OAuth, login, logout, etc.)
    # Provides: /accounts/login/, /accounts/logout/, /accounts/google/login/callback/, etc.
    path('accounts/', include('allauth.urls')),

    # All appointment system URLs
    path('', include('appointments.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

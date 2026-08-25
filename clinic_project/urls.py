# ============================================================
# clinic_project/urls.py — Root URL Configuration
# ============================================================
# All routes are delegated to the 'appointments' app.
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # All appointment system URLs
    path('', include('appointments.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

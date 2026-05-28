# ============================================================
# clinic_project/__init__.py
# Django Project Initialization
# ============================================================
"""
Ensures Celery app is imported on Django startup.
"""

# Import the Celery app to ensure it's always initialized
from .celery import app as celery_app

__all__ = ['celery_app']

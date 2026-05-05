# ============================================================
# appointments/decorators.py — Role-Based Access Control
# ============================================================

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to access this page.')
                return redirect('login')
            if hasattr(request.user, 'profile'):
                if request.user.profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return wrapper
    return decorator


def doctor_required(view_func):
    return role_required(['doctor'])(view_func)


def patient_required(view_func):
    return role_required(['patient'])(view_func)


def admin_required(view_func):
    return role_required(['admin'])(view_func)

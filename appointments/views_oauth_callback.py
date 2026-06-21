"""
appointments/views_oauth_callback.py - Professional OAuth Callback Handler
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import IntegrityError
from .models import Profile, Patient, Doctor


class GoogleOAuthCallbackView(View):
    """
    Professional handler for Google OAuth callback.
    Processes the returned OAuth data and creates/updates user profile.
    """
    template_name = 'oauth/google_callback.html'

    def get(self, request):
        """
        After Google OAuth completes, this view:
        1. Checks if user is authenticated
        2. Creates Patient profile if needed
        3. Redirects to dashboard or onboarding
        """
        # If there was an error in OAuth flow, show it
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        if error:
            messages.error(request, f'Google login failed: {error_description or error}')
            return redirect('login')

        # If user is authenticated (OAuth succeeded)
        if request.user.is_authenticated:
            try:
                # Ensure user has a profile
                profile, _ = Profile.objects.get_or_create(user=request.user)
                
                # If role not set, assume patient
                if not profile.role:
                    profile.role = 'patient'
                    profile.save()
                
                # Create patient record if needed
                if profile.role == 'patient':
                    Patient.objects.get_or_create(user=request.user)
                
                # Show success and redirect
                messages.success(request, f'Welcome, {request.user.first_name or request.user.username}! 🎉')
                return redirect('dashboard')
            
            except IntegrityError:
                messages.warning(request, 'Account setup in progress. Please wait...')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, 'An error occurred during account setup.')
                return redirect('home')
        
        # Not authenticated - shouldn't happen, but fallback to login
        messages.error(request, 'Authentication failed. Please try again.')
        return redirect('login')


class GoogleOAuthLoadingView(View):
    """
    Shows a professional loading screen while redirecting to Google OAuth.
    Provides better UX than instant redirect.
    """
    template_name = 'oauth/google_redirect.html'
    
    def get(self, request):
        """Display loading page during redirect to Google"""
        return render(request, self.template_name)

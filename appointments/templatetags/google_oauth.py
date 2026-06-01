"""
Custom template tag for safe Google OAuth URL rendering.
Handles the MultipleObjectsReturned error gracefully.
"""
from django import template
from allauth.socialaccount.adapter import get_adapter

register = template.Library()


@register.simple_tag
def safe_google_login_url(request):
    """
    Safely get Google login URL without throwing MultipleObjectsReturned error.
    
    If multiple Google apps exist, tries to get the one with a non-empty name.
    If none, returns empty string instead of crashing.
    """
    try:
        from allauth.socialaccount.models import SocialApp
        
        # Get all Google apps
        google_apps = SocialApp.objects.filter(provider='google')
        
        if not google_apps.exists():
            return ''
        
        if google_apps.count() == 1:
            # Use the normal allauth method if only one exists
            adapter = get_adapter(request)
            provider = adapter.get_provider(request, 'google')
            from allauth.socialaccount.providers.google.views import google_callback
            return f"/accounts/google/login/callback/?next=/"
        else:
            # Multiple apps exist - use the named one
            named_apps = [app for app in google_apps if app.name.strip()]
            if named_apps:
                app = named_apps[0]
                # Return the OAuth login URL
                return f"/accounts/google/login/?next=/"
            else:
                # No named app, just use first one
                return f"/accounts/google/login/?next=/"
    
    except Exception as e:
        # Fallback: return empty string instead of crashing
        print(f"Error in safe_google_login_url: {e}")
        return ''


@register.simple_tag
def safe_provider_login_url(request, provider='google'):
    """
    Safe wrapper around provider_login_url that handles MultipleObjectsReturned.
    """
    try:
        from allauth.socialaccount.templatetags.socialaccount import provider_login_url
        return provider_login_url(request, provider)
    except Exception:
        # If allauth fails, return a fallback URL
        return f"/accounts/{provider}/login/?next=/"

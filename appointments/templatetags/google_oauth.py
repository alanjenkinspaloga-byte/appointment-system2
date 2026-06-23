"""
Custom template tag for safe Google OAuth URL rendering.
Handles the MultipleObjectsReturned error gracefully and auto-fixes duplicates.
Generates direct Google OAuth authorization URL to skip Django intermediate page.
"""
from django import template
from django.utils.decorators import sync_and_async_middleware
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def safe_provider_login_url(request, provider='google'):
    """
    Safe wrapper that generates direct Google OAuth authorization URL.
    
    Automatically cleans up duplicate Google OAuth apps on first use.
    Returns the direct Google OAuth consent URL, skipping any Django intermediate pages.
    """
    try:
        from allauth.socialaccount.models import SocialApp
        from django.urls import reverse
        from django.conf import settings
        
        if provider != 'google':
            # For non-Google providers, use the standard method
            try:
                from allauth.socialaccount.templatetags.socialaccount import provider_login_url as allauth_login
                return allauth_login(request, provider)
            except Exception:
                return f"/accounts/{provider}/login/?next=/"
        
        # Handle Google OAuth specifically
        google_apps = SocialApp.objects.filter(provider='google')
        
        if not google_apps.exists():
            return ''
        
        # Auto-cleanup: if multiple apps exist, fix it automatically
        if google_apps.count() > 1:
            # Find named and unnamed apps
            named_apps = [app for app in google_apps if app.name.strip()]
            unnamed_apps = [app for app in google_apps if not app.name.strip()]
            
            # Decide which one to keep
            if named_apps:
                to_keep = named_apps[0]
                to_delete = unnamed_apps + named_apps[1:]
            else:
                to_keep = google_apps[0]
                to_delete = google_apps[1:]
            
            # Delete duplicates
            for app in to_delete:
                app.delete()
            
            # Log the cleanup (optional)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Auto-cleaned {len(to_delete)} duplicate Google OAuth apps. Kept ID={to_keep.id}")
        
        # Get the Google app credentials
        google_app = SocialApp.objects.filter(provider='google').first()
        if not google_app:
            return ''
        
        # Get the callback URL from the adapter
        try:
            from allauth.socialaccount.adapter import get_adapter
            adapter = get_adapter(request)
            provider = adapter.get_provider(request, 'google')
            callback_url = provider.get_callback_url(request)
        except Exception:
            # Fallback: construct the callback URL manually
            from django.urls import reverse
            callback_url = request.build_absolute_uri(reverse('socialaccount_callback', args=['google']))
        
        # Build direct Google OAuth authorization URL
        google_oauth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        
        params = {
            'client_id': google_app.client_id,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'scope': 'openid profile email',
            'access_type': 'offline',
            'prompt': 'consent',  # Always show account selection
        }
        
        return f"{google_oauth_url}?{urlencode(params)}"
    
    except Exception as e:
        # Fallback: return empty string instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error in safe_provider_login_url: {e}")
        return ''

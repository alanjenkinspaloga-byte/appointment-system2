"""
Custom template tag for safe Google OAuth URL rendering.
Handles the MultipleObjectsReturned error gracefully and auto-fixes duplicates.
Generates direct Google OAuth authorization URL to skip Django intermediate page.
"""
from django import template
from django.utils.decorators import sync_and_async_middleware
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag
def safe_provider_login_url(request, provider='google'):
    """
    Safe wrapper that generates direct Google OAuth authorization URL.
    
    Automatically cleans up duplicate Google OAuth apps on first use.
    Returns the direct Google OAuth consent URL, skipping any Django intermediate pages.
    Falls back to allauth's standard URL if direct generation fails.
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
            logger.error("No Google OAuth app found in database - falling back to allauth URL")
            return "/accounts/google/login/?next=/"
        
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
            
            logger.info(f"Auto-cleaned {len(to_delete)} duplicate Google OAuth apps. Kept ID={to_keep.id}")
        
        # Get the Google app credentials
        google_app = SocialApp.objects.filter(provider='google').first()
        if not google_app:
            logger.error("Google OAuth app not found after cleanup - falling back to allauth URL")
            return "/accounts/google/login/?next=/"
        
        if not google_app.client_id:
            logger.error(f"Google OAuth app (ID={google_app.id}) has no client_id configured - falling back to allauth URL")
            return "/accounts/google/login/?next=/"
        
        logger.info(f"Using Google OAuth app: {google_app.name} (ID={google_app.id}, client_id={google_app.client_id[:20]}...)")
        
        # Get the callback URL from the adapter
        try:
            from allauth.socialaccount.adapter import get_adapter
            adapter = get_adapter(request)
            oauth_provider = adapter.get_provider(request, 'google')
            callback_url = oauth_provider.get_callback_url(request)
            logger.info(f"Using callback URL: {callback_url}")
        except Exception as e:
            # Fallback: construct the callback URL manually
            logger.warning(f"Failed to get callback URL from adapter: {e}, using fallback")
            try:
                callback_url = request.build_absolute_uri(reverse('socialaccount_callback', args=['google']))
            except Exception as e2:
                logger.error(f"Failed to build callback URL: {e2} - falling back to allauth URL")
                return "/accounts/google/login/?next=/"
        
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
        
        final_url = f"{google_oauth_url}?{urlencode(params)}"
        logger.info(f"Generated direct OAuth URL (length: {len(final_url)} chars)")
        return final_url
    
    except Exception as e:
        # Fallback to allauth's default URL
        logger.exception(f"Error in safe_provider_login_url: {e} - falling back to allauth URL")
        return "/accounts/google/login/?next=/"

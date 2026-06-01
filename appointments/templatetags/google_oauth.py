"""
Custom template tag for safe Google OAuth URL rendering.
Handles the MultipleObjectsReturned error gracefully and auto-fixes duplicates.
"""
from django import template
from django.utils.decorators import sync_and_async_middleware

register = template.Library()


@register.simple_tag
def safe_provider_login_url(request, provider='google'):
    """
    Safe wrapper around provider_login_url that handles MultipleObjectsReturned.
    
    Automatically cleans up duplicate Google OAuth apps on first use.
    If multiple apps exist, keeps the named one and deletes unnamed ones.
    """
    try:
        from allauth.socialaccount.models import SocialApp
        
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
        
        # Now use the standard allauth method
        try:
            from allauth.socialaccount.adapter import get_adapter
            adapter = get_adapter(request)
            # After cleanup, there should be only one app, so this should work
            provider_obj = adapter.get_provider(request, provider)
            return f"/accounts/google/login/?next=/"
        except Exception:
            # Fallback
            return f"/accounts/google/login/?next=/"
    
    except Exception as e:
        # Fallback: return empty string instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error in safe_provider_login_url: {e}")
        return ''

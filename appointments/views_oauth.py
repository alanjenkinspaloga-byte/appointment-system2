from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import MultipleObjectsReturned
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class SafeSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that auto-cleans duplicate Google OAuth apps,
    preventing MultipleObjectsReturned errors during OAuth flow.
    
    This adapter ensures OAuth logins work even with duplicate SocialApp records
    by automatically cleaning them up during the authentication process.
    """
    
    def get_app(self, request, provider, client_id=None):
        """
        Override get_app with comprehensive duplicate handling for all providers.
        
        For Google provider specifically:
        - Tries to get the app normally first
        - If MultipleObjectsReturned, auto-cleans duplicates
        - Retries after cleanup
        - Falls back to first available app if needed
        
        This ensures OAuth flow doesn't break even with duplicate app records.
        """
        try:
            # Check if we have duplicates BEFORE calling super()
            if provider == 'google':
                apps = list(SocialApp.objects.filter(provider='google'))
                if len(apps) > 1:
                    logger.warning(
                        f"Detected {len(apps)} Google OAuth apps. "
                        f"Cleaning up duplicates before OAuth flow..."
                    )
                    self._cleanup_provider_duplicates(provider, force=True)
                    # After cleanup, refresh the query
                    apps = list(SocialApp.objects.filter(provider='google'))
            
            # Try to get the app normally
            return super().get_app(request, provider, client_id)
        
        except MultipleObjectsReturned as e:
            # Multiple apps found for this provider (fallback catch)
            logger.warning(
                f"MultipleObjectsReturned caught for provider '{provider}' - "
                f"attempting emergency cleanup..."
            )
            
            if provider == 'google':
                try:
                    # Emergency cleanup with force flag
                    self._cleanup_provider_duplicates(provider, force=True)
                    
                    # Retry after cleanup
                    try:
                        return super().get_app(request, provider, client_id)
                    except MultipleObjectsReturned:
                        logger.error(
                            f"Still have duplicates after cleanup for '{provider}'. "
                            f"Using emergency fallback..."
                        )
                        return self._get_fallback_app(provider)
                
                except Exception as cleanup_error:
                    logger.error(
                        f"Error during emergency duplicate cleanup: {cleanup_error}. "
                        f"Attempting fallback...",
                        exc_info=True
                    )
                    try:
                        return self._get_fallback_app(provider)
                    except Exception as fallback_error:
                        logger.critical(
                            f"Both cleanup and fallback failed for '{provider}': "
                            f"{fallback_error}",
                            exc_info=True
                        )
                        raise
            
            # For non-Google providers, re-raise
            logger.error(
                f"MultipleObjectsReturned for non-Google provider '{provider}'. "
                f"Manual cleanup required."
            )
            raise
    
    def _cleanup_provider_duplicates(self, provider, force=False):
        """
        Clean up duplicate OAuth apps for a specific provider, keeping one with valid config.
        
        Args:
            provider: The OAuth provider name (e.g., 'google')
            force: If True, forces cleanup even without validation checks
        
        Returns True if cleanup was successful or no duplicates exist, False if error occurs.
        """
        from django.db import transaction as db_transaction
        
        try:
            apps = list(SocialApp.objects.filter(provider=provider).order_by('id'))
            
            if len(apps) <= 1:
                logger.info(f"No duplicates found for provider '{provider}'")
                return True
            
            logger.warning(
                f"Found {len(apps)} apps for '{provider}': "
                f"{[(app.id, app.name) for app in apps]}"
            )
            
            # Prioritize which app to keep (named > unnamed)
            named_apps = [app for app in apps if app.name and app.name.strip()]
            unnamed_apps = [app for app in apps if not app.name or not app.name.strip()]
            
            if named_apps:
                # Prefer app with a name
                to_keep = named_apps[0]
                to_delete = unnamed_apps + named_apps[1:]
                logger.info(f"Keeping named app: {to_keep.name} (ID={to_keep.id})")
            else:
                # All unnamed, keep first by ID
                to_keep = apps[0]
                to_delete = apps[1:]
                logger.warning(f"All apps unnamed, keeping ID={to_keep.id}")
            
            if not to_delete:
                logger.info(f"No duplicates to delete for '{provider}'")
                return True
            
            deleted_ids = [app.id for app in to_delete]
            
            # Delete duplicates in transaction
            with db_transaction.atomic():
                for app in to_delete:
                    try:
                        app.delete()
                        logger.info(f"Deleted duplicate app ID={app.id}, Name='{app.name}'")
                    except Exception as delete_error:
                        logger.error(f"Error deleting app ID={app.id}: {delete_error}")
                        if not force:
                            raise
            
            logger.warning(
                f"✓ Cleaned up {len(to_delete)} duplicate(s) for '{provider}': "
                f"kept ID={to_keep.id}, deleted IDs={deleted_ids}"
            )
            return True
        
        except Exception as e:
            logger.error(
                f"Error cleaning up duplicates for '{provider}': {e}",
                exc_info=True
            )
            return False if not force else True  # Force mode continues despite errors
    
    def _get_fallback_google_duplicates(self):
        """
        DEPRECATED: Use _get_fallback_app() instead.
        Kept for backward compatibility.
        """
        return self._get_fallback_app('google')
    
    def _get_fallback_app(self, provider):
        """
        Return the first available and valid app for the given provider as fallback.
        This is the emergency fallback when duplicates exist.
        """
        try:
            # Try to get app with client_id first (more likely to be valid)
            app = SocialApp.objects.filter(
                provider=provider
            ).exclude(
                client_id__in=['', None]
            ).order_by('id').first()
            
            if app:
                logger.warning(
                    f"Fallback: Using app with valid client_id for '{provider}': "
                    f"ID={app.id}, Name='{app.name}'"
                )
                return app
            
            # If no valid client_id, just get any app
            app = SocialApp.objects.filter(provider=provider).order_by('id').first()
            if app:
                logger.warning(
                    f"Fallback: Using first available app for '{provider}': "
                    f"ID={app.id}, Name='{app.name}'"
                )
                return app
            
            raise ValueError(
                f"No {provider.upper()} OAuth apps found in database. "
                f"Run: python manage.py setup_google_oauth"
            )
        except Exception as e:
            logger.error(f"Fallback retrieval failed for '{provider}': {e}")
            raise


@require_http_methods(["GET"])
@staff_member_required
def cleanup_duplicate_google_oauth(request):
    """
    Admin-only view to clean up duplicate Google OAuth apps.
    
    Access via: /admin/cleanup-google-oauth/
    Requires staff/admin login
    
    Note: For production environments, prefer using the management command:
      python manage.py cleanup_google_oauth_duplicates
    """
    try:
        google_apps = SocialApp.objects.filter(provider='google')
        
        if not google_apps.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No Google OAuth apps found in database',
                'action': 'Run: python manage.py setup_google_oauth'
            })
        
        apps_before = google_apps.count()
        
        if apps_before == 1:
            return JsonResponse({
                'status': 'success',
                'message': f'✓ Only one Google OAuth app exists (ID={google_apps.first().id}). No cleanup needed.',
                'apps_before': 1,
                'apps_after': 1
            })
        
        # Multiple apps exist - clean up
        named_apps = [app for app in google_apps if app.name.strip()]
        unnamed_apps = [app for app in google_apps if not app.name.strip()]
        
        if named_apps:
            to_keep = named_apps[0]
            to_delete = unnamed_apps + named_apps[1:]
        else:
            to_keep = google_apps.order_by('id').first()
            to_delete = [app for app in google_apps if app.id != to_keep.id]
        
        deleted_ids = [app.id for app in to_delete]
        
        with transaction.atomic():
            for app in to_delete:
                app.delete()
        
        logger.info(
            f"Cleaned up {len(to_delete)} duplicate Google OAuth apps via web interface. "
            f"Kept ID={to_keep.id}, deleted IDs={deleted_ids}"
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'✓ Cleanup complete! Kept app ID={to_keep.id} ("{to_keep.name}"), '
                      f'deleted {len(to_delete)} duplicate(s).',
            'apps_before': apps_before,
            'apps_after': 1,
            'kept_app_id': to_keep.id,
            'kept_app_name': to_keep.name,
            'deleted_ids': deleted_ids
        })
    
    except Exception as e:
        logger.error(f"Error during cleanup via web interface: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error during cleanup: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@staff_member_required
def debug_google_oauth_config(request):
    """
    Admin-only endpoint to debug Google OAuth configuration.
    
    Access via: /debug-oauth-config/
    Shows database config and template tag output for debugging.
    """
    try:
        from appointments.templatetags.google_oauth import safe_provider_login_url
        
        google_apps = SocialApp.objects.filter(provider='google')
        
        debug_info = {
            'status': 'debug',
            'google_apps_count': google_apps.count(),
            'apps': [],
            'template_tag_url': safe_provider_login_url(request, 'google'),
        }
        
        for app in google_apps:
            debug_info['apps'].append({
                'id': app.id,
                'name': app.name,
                'provider': app.provider,
                'client_id': f"{app.client_id[:20]}..." if app.client_id else 'MISSING',
                'has_secret': bool(app.secret),
                'sites': list(app.sites.values_list('domain', flat=True))
            })
        
        return JsonResponse(debug_info)
    
    except Exception as e:
        logger.exception(f"Error in debug endpoint: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Debug error: {str(e)}'
        }, status=500)

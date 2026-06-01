from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SafeSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that auto-cleans duplicate Google OAuth apps
    before trying to fetch them.
    
    This prevents MultipleObjectsReturned errors during OAuth flow.
    """
    
    def get_app(self, request, provider, client_id=None):
        """
        Override get_app to auto-clean duplicates before fetching.
        """
        # Auto-cleanup for Google provider
        if provider == 'google':
            google_apps = SocialApp.objects.filter(provider='google')
            
            if google_apps.count() > 1:
                # Multiple apps exist - clean them up
                named_apps = [app for app in google_apps if app.name.strip()]
                unnamed_apps = [app for app in google_apps if not app.name.strip()]
                
                if named_apps:
                    to_keep = named_apps[0]
                    to_delete = unnamed_apps + named_apps[1:]
                else:
                    to_keep = google_apps[0]
                    to_delete = google_apps[1:]
                
                # Delete duplicates
                deleted_count = len(to_delete)
                for app in to_delete:
                    app.delete()
                
                # Log the cleanup
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"SafeSocialAccountAdapter: Auto-cleaned {deleted_count} duplicate Google OAuth apps. Kept ID={to_keep.id}")
        
        # Call parent method (now with clean data)
        return super().get_app(request, provider, client_id)


@require_http_methods(["GET"])
@staff_member_required
def cleanup_duplicate_google_oauth(request):
    """
    Admin-only view to clean up duplicate Google OAuth apps.
    
    Access via: /admin/cleanup-google-oauth/
    Requires staff/admin login
    """
    try:
        google_apps = SocialApp.objects.filter(provider='google')
        
        if not google_apps.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No Google OAuth apps found in database'
            })
        
        if google_apps.count() == 1:
            return JsonResponse({
                'status': 'success',
                'message': f'✓ Only one Google OAuth app exists (ID={google_apps.first().id}). No cleanup needed.',
                'apps_before': 1,
                'apps_after': 1
            })
        
        # Multiple apps exist - clean up
        named_apps = [app for app in google_apps if app.name.strip()]
        unnamed_apps = [app for app in google_apps if not app.name.strip()]
        
        apps_before = google_apps.count()
        
        if named_apps:
            to_keep = named_apps[0]
            to_delete = unnamed_apps + named_apps[1:]
        else:
            to_keep = google_apps[0]
            to_delete = google_apps[1:]
        
        deleted_ids = [app.id for app in to_delete]
        for app in to_delete:
            app.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'✓ Cleanup complete! Kept app ID={to_keep.id} ("{to_keep.name}"), deleted {len(to_delete)} duplicates.',
            'apps_before': apps_before,
            'apps_after': 1,
            'kept_app_id': to_keep.id,
            'kept_app_name': to_keep.name,
            'deleted_ids': deleted_ids
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error during cleanup: {str(e)}'
        }, status=500)

"""
Management command to diagnose Google OAuth setup issues.

This command checks:
1. If Google OAuth apps exist in the database
2. If there are duplicates
3. If the apps are properly configured
4. If the Site configuration is correct

Usage:
    python manage.py diagnose_google_oauth
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


class Command(BaseCommand):
    help = 'Diagnose Google OAuth setup and identify issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Google OAuth Diagnostics'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # 1. Check Site configuration
        self.stdout.write('1. Checking Site Configuration...')
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(self.style.SUCCESS(f'   ✓ Site ID=1 exists: "{site.name}" ({site.domain})'))
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ Site ID=1 does not exist'))
            self.stdout.write(self.style.WARNING('   → Run: python manage.py migrate'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error checking site: {e}'))

        # 2. Check Google OAuth apps
        self.stdout.write('\n2. Checking Google OAuth Apps...')
        google_apps = SocialApp.objects.filter(provider='google')
        
        if not google_apps.exists():
            self.stdout.write(self.style.ERROR('   ✗ No Google OAuth apps found'))
            self.stdout.write(self.style.WARNING('   → Run: python manage.py setup_google_oauth'))
        else:
            count = google_apps.count()
            if count == 1:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Found 1 Google OAuth app (expected)'))
                app = google_apps.first()
                self._display_app_details(app)
            else:
                self.stdout.write(self.style.ERROR(f'   ✗ Found {count} Google OAuth apps (expected 1)'))
                for i, app in enumerate(google_apps):
                    self.stdout.write(f'\n   App {i+1}:')
                    self._display_app_details(app, indent=3)
                self.stdout.write(self.style.WARNING('\n   → Run: python manage.py cleanup_duplicate_google_oauth'))

        # 3. Check app-site associations
        self.stdout.write('\n3. Checking App-Site Associations...')
        if google_apps.exists():
            for app in google_apps:
                if app.sites.filter(id=1).exists():
                    self.stdout.write(self.style.SUCCESS(f'   ✓ App ID={app.id} is associated with Site ID=1'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠ App ID={app.id} is NOT associated with Site ID=1'))
                    self.stdout.write(f'     Associated with sites: {", ".join(str(s.id) for s in app.sites.all())}')

        # 4. Check Django settings
        self.stdout.write('\n4. Checking Django Settings...')
        adapter = getattr(settings, 'SOCIALACCOUNT_ADAPTER', 'default')
        self.stdout.write(f'   SOCIALACCOUNT_ADAPTER: {adapter}')
        
        if adapter == 'appointments.views_oauth.SafeSocialAccountAdapter':
            self.stdout.write(self.style.SUCCESS('   ✓ Using SafeSocialAccountAdapter (auto-cleanup enabled)'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠ Not using SafeSocialAccountAdapter'))

        site_id = getattr(settings, 'SITE_ID', None)
        if site_id == 1:
            self.stdout.write(self.style.SUCCESS('   ✓ SITE_ID = 1'))
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ SITE_ID = {site_id} (expected 1)'))

        providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
        if 'google' in providers:
            self.stdout.write(self.style.SUCCESS('   ✓ Google provider configured in SOCIALACCOUNT_PROVIDERS'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ Google provider NOT configured'))

        # 5. Summary and recommendations
        self.stdout.write('\n' + '='*70)
        self.stdout.write('Summary & Recommendations:')
        self.stdout.write('='*70 + '\n')

        if google_apps.count() == 1 and google_apps.first().sites.filter(id=1).exists():
            self.stdout.write(self.style.SUCCESS('✓ Your Google OAuth setup appears to be correct!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('  1. Visit /accounts/login/')
            self.stdout.write('  2. Click "Sign in with Google"')
            self.stdout.write('  3. Complete the Google OAuth flow')
        else:
            self.stdout.write(self.style.ERROR('✗ Issues detected. Follow these steps:'))
            self.stdout.write('\n  Option A - Quick Fix:')
            self.stdout.write('    1. python manage.py migrate')
            self.stdout.write('    2. python manage.py setup_google_oauth')
            self.stdout.write('    3. python manage.py diagnose_google_oauth')
            self.stdout.write('\n  Option B - Manual Cleanup:')
            self.stdout.write('    1. python manage.py cleanup_duplicate_google_oauth')
            self.stdout.write('    2. python manage.py setup_google_oauth')

        self.stdout.write('\n' + '='*70 + '\n')

    def _display_app_details(self, app, indent=2):
        """Display details of a SocialApp."""
        prefix = ' ' * indent
        self.stdout.write(f'{prefix}ID: {app.id}')
        self.stdout.write(f'{prefix}Name: "{app.name}"')
        self.stdout.write(f'{prefix}Provider: {app.provider}')
        self.stdout.write(f'{prefix}Client ID: {app.client_id[:20]}...' if app.client_id else f'{prefix}Client ID: (empty)')
        self.stdout.write(f'{prefix}Secret: {"(set)" if app.secret else "(empty)"}')
        sites = ', '.join(f'{s.id}' for s in app.sites.all())
        self.stdout.write(f'{prefix}Associated Sites: {sites if sites else "(none)"}')

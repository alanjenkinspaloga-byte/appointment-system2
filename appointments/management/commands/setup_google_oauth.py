# appointments/management/commands/setup_google_oauth.py
"""
Management command to set up Google OAuth app in Django admin.

This command creates or updates the SocialApp for Google in the Site framework,
which is required by django-allauth for Google OAuth to work.

Usage:
    python manage.py setup_google_oauth --client-id YOUR_CLIENT_ID --secret YOUR_SECRET
    python manage.py setup_google_oauth  # Read from .env
"""

from django.core.management.base import BaseCommand, CommandError
from decouple import config
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up Google OAuth app in Django admin (required for django-allauth to work)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth 2.0 Client ID',
        )
        parser.add_argument(
            '--secret',
            type=str,
            help='Google OAuth 2.0 Client Secret',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Google OAuth Setup for django-allauth'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Get credentials from arguments or environment
        client_id = options.get('client_id') or config('GOOGLE_OAUTH_CLIENT_ID', default='')
        secret = options.get('secret') or config('GOOGLE_OAUTH_CLIENT_SECRET', default='')

        if not client_id or not secret:
            self.stdout.write(
                self.style.ERROR(
                    '✗ Missing Google OAuth credentials!\n'
                    'Please provide:\n'
                    '  1. Via command: python manage.py setup_google_oauth --client-id YOUR_ID --secret YOUR_SECRET\n'
                    '  2. Via .env file: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET\n'
                )
            )
            raise CommandError('Missing Google OAuth credentials')

        try:
            with transaction.atomic():
                # Get or create the default Site
                site = Site.objects.get_or_create(
                    id=1,
                    defaults={
                        'domain': 'localhost:8000',
                        'name': 'OkiDoki Clinic'
                    }
                )[0]

                self.stdout.write(f'✓ Site: {site.name} ({site.domain})')

                # Clean up any duplicate Google apps (keep only one)
                google_apps = SocialApp.objects.filter(provider='google').order_by('id')
                
                if google_apps.count() > 1:
                    self.stdout.write(self.style.WARNING(f'\n⚠ Found {google_apps.count()} duplicate Google OAuth apps. Cleaning up...'))
                    # Keep the first one by ID, delete others
                    to_keep = google_apps.first()
                    to_delete = list(google_apps[1:])
                    
                    deleted_ids = [app.id for app in to_delete]
                    for app in to_delete:
                        app.delete()
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted {len(to_delete)} duplicate app(s) (IDs: {deleted_ids})'))
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Kept app ID={to_keep.id} ("{to_keep.name}")'))
                    
                    google_apps = SocialApp.objects.filter(provider='google')

                # Get or create Google SocialApp
                if google_apps.exists():
                    google_app = google_apps.first()
                    google_app.client_id = client_id
                    google_app.secret = secret
                    google_app.save()
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Updated Google OAuth App'))
                else:
                    google_app = SocialApp.objects.create(
                        provider='google',
                        name='Google OAuth',
                        client_id=client_id,
                        secret=secret,
                    )
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Created Google OAuth App'))

                # Associate app with site
                if site not in google_app.sites.all():
                    google_app.sites.add(site)
                    self.stdout.write(f'✓ Associated app with site: {site.name}')
                else:
                    self.stdout.write(f'✓ App already associated with site: {site.name}')

            self.stdout.write(self.style.SUCCESS('\n✓ Google OAuth Setup Complete!\n'))
            self.stdout.write(
                self.style.WARNING(
                    'Next Steps:\n'
                    '  1. Ensure .env has GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET\n'
                    '  2. In Google Cloud Console, add this Redirect URI to your OAuth app:\n'
                    '     http://localhost:8000/accounts/google/login/callback/ (development)\n'
                    '     https://yourdomain.com/accounts/google/login/callback/ (production)\n'
                    '  3. Run: python manage.py diagnose_google_oauth (to verify setup)\n'
                    '  4. Visit /accounts/login/ to test Google sign-in\n'
                )
            )
            
            # Run diagnostics
            self.stdout.write('\n' + '='*70)
            self.stdout.write('Setup Verification:')
            self.stdout.write('='*70)
            final_apps = SocialApp.objects.filter(provider='google')
            self.stdout.write(f'✓ Google OAuth apps in database: {final_apps.count()}')
            if final_apps.exists():
                app = final_apps.first()
                self.stdout.write(f'✓ Client ID configured: {bool(app.client_id)}')
                self.stdout.write(f'✓ Secret configured: {bool(app.secret)}')
                self.stdout.write(f'✓ Associated with site: {site in app.sites.all()}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to set up Google OAuth: {str(e)}')

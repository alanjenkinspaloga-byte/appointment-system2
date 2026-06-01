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
            google_apps = SocialApp.objects.filter(provider='google')
            if google_apps.count() > 1:
                self.stdout.write(self.style.WARNING(f'\n⚠ Found {google_apps.count()} duplicate Google OAuth apps. Cleaning up...'))
                # Keep the named one, delete others
                named = [a for a in google_apps if a.name.strip()]
                unnamed = [a for a in google_apps if not a.name.strip()]
                
                to_delete = unnamed + named[1:]
                for app in to_delete:
                    app.delete()
                    self.stdout.write(f'  ✓ Deleted duplicate app (ID={app.id})')
                
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

            self.stdout.write(self.style.SUCCESS('\n✓ Google OAuth Setup Complete!\n'))
            self.stdout.write(
                self.style.WARNING(
                    'Next Steps:\n'
                    '  1. Update .env with GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET\n'
                    '  2. In Google Cloud Console, add this Redirect URI to your OAuth app:\n'
                    '     http://localhost:8000/accounts/google/login/callback/ (development)\n'
                    '     https://yourdomain.com/accounts/google/login/callback/ (production)\n'
                    '  3. Visit /accounts/login/ to test Google sign-in\n'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}\n'))
            raise CommandError(f'Failed to set up Google OAuth: {str(e)}')

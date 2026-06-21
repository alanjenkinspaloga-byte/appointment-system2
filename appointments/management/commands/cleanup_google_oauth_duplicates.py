# appointments/management/commands/cleanup_google_oauth_duplicates.py
"""
Management command to clean up duplicate Google OAuth apps and diagnose issues.

Usage:
    python manage.py cleanup_google_oauth_duplicates           # Show status and cleanup if needed
    python manage.py cleanup_google_oauth_duplicates --force    # Force cleanup even if only one app
    python manage.py cleanup_google_oauth_duplicates --dry-run  # Show what would be deleted without deleting
"""

from django.core.management.base import BaseCommand, CommandError
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.db import transaction


class Command(BaseCommand):
    help = 'Clean up duplicate Google OAuth apps and verify setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even if only one app exists',
        )
        parser.add_argument(
            '--keep-id',
            type=int,
            help='Specify which app ID to keep (default: keeps first by ID)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Google OAuth Duplicate Cleanup Utility'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        keep_id = options.get('keep_id')

        try:
            # Step 1: Diagnose current state
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 1] Diagnosing Current State'))
            self.stdout.write('-' * 70)
            
            google_apps = SocialApp.objects.filter(provider='google').order_by('id')
            total_apps = google_apps.count()
            
            self.stdout.write(f'Google OAuth apps in database: {total_apps}')
            
            if total_apps == 0:
                self.stdout.write(self.style.WARNING('⚠ No Google OAuth apps found!'))
                self.stdout.write('  → Run: python manage.py setup_google_oauth\n')
                return
            
            # Show all apps
            self.stdout.write('\nApps Details:')
            for i, app in enumerate(google_apps, 1):
                self.stdout.write(f'  {i}. ID={app.id} | Name="{app.name}" | Client ID: {app.client_id[:20]}...' if len(app.client_id) > 20 else f'  {i}. ID={app.id} | Name="{app.name}" | Client ID: {app.client_id}')
                sites = list(app.sites.values_list('name', flat=True))
                self.stdout.write(f'     Sites: {", ".join(sites) if sites else "(none)"}')
            
            # Step 2: Determine if cleanup is needed
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 2] Analyzing Duplicates'))
            self.stdout.write('-' * 70)
            
            if total_apps == 1:
                if not force:
                    self.stdout.write(self.style.SUCCESS('✓ Only one Google OAuth app exists. No cleanup needed.\n'))
                    self._verify_configuration(google_apps.first())
                    return
                else:
                    self.stdout.write(self.style.WARNING('⚠ --force flag used, but only one app exists. Skipping cleanup.'))
                    return
            
            self.stdout.write(self.style.WARNING(f'⚠ Found {total_apps} Google OAuth apps (duplicates detected!)'))
            self.stdout.write(f'  → Will keep: 1 app')
            self.stdout.write(f'  → Will delete: {total_apps - 1} app(s)')
            
            # Step 3: Determine which to keep
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 3] Selecting App to Keep'))
            self.stdout.write('-' * 70)
            
            if keep_id:
                # Keep specific app
                to_keep = google_apps.filter(id=keep_id).first()
                if not to_keep:
                    raise CommandError(f'App with ID={keep_id} not found')
                self.stdout.write(f'Using --keep-id: ID={to_keep.id} ("{to_keep.name}")')
            else:
                # Prefer named apps, fallback to first by ID
                named_apps = [app for app in google_apps if app.name.strip()]
                if named_apps:
                    to_keep = named_apps[0]
                    self.stdout.write(f'Selected named app: ID={to_keep.id} ("{to_keep.name}")')
                else:
                    to_keep = google_apps.first()
                    self.stdout.write(f'Selected first app by ID: ID={to_keep.id}')
            
            to_delete = [app for app in google_apps if app.id != to_keep.id]
            
            # Step 4: Show cleanup preview
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 4] Cleanup Preview'))
            self.stdout.write('-' * 70)
            self.stdout.write(f'To Keep: ID={to_keep.id} ("{to_keep.name}")')
            self.stdout.write(f'To Delete: {len(to_delete)} app(s)')
            for app in to_delete:
                self.stdout.write(f'  • ID={app.id} ("{app.name}")')
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS('\n[DRY RUN] No changes made.\n'))
                return
            
            # Step 5: Execute cleanup
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 5] Executing Cleanup'))
            self.stdout.write('-' * 70)
            
            try:
                with transaction.atomic():
                    deleted_ids = [app.id for app in to_delete]
                    for app in to_delete:
                        app.delete()
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ Successfully deleted {len(to_delete)} duplicate app(s)'))
                    self.stdout.write(f'  Deleted IDs: {deleted_ids}')
            
            except Exception as e:
                raise CommandError(f'Failed to delete duplicates: {str(e)}')
            
            # Step 6: Verify cleanup
            self.stdout.write(self.style.MIGRATE_HEADING('\n[STEP 6] Verification'))
            self.stdout.write('-' * 70)
            
            final_apps = SocialApp.objects.filter(provider='google')
            final_count = final_apps.count()
            
            if final_count == 1:
                self.stdout.write(self.style.SUCCESS(f'✓ Cleanup successful! Only 1 Google OAuth app remains.'))
                self._verify_configuration(final_apps.first())
            else:
                self.stdout.write(self.style.ERROR(f'✗ Cleanup failed! Still have {final_count} apps'))
                raise CommandError('Cleanup did not resolve the issue')
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*70))
            self.stdout.write(self.style.SUCCESS('✓ Google OAuth Setup is now clean!'))
            self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
            
        except Exception as e:
            if isinstance(e, CommandError):
                raise
            raise CommandError(f'Error: {str(e)}')

    def _verify_configuration(self, app):
        """Verify Google OAuth app is properly configured."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n[Configuration Check]'))
        self.stdout.write('-' * 70)
        
        checks = {
            'App Name': bool(app.name.strip()),
            'Client ID': bool(app.client_id),
            'Secret': bool(app.secret),
            'Associated with Site': app.sites.exists(),
        }
        
        for check_name, is_ok in checks.items():
            status = self.style.SUCCESS('✓') if is_ok else self.style.ERROR('✗')
            self.stdout.write(f'{status} {check_name}')
        
        if not all(checks.values()):
            self.stdout.write(self.style.WARNING('\n⚠ Some configuration issues detected. Run:'))
            self.stdout.write('  python manage.py setup_google_oauth\n')

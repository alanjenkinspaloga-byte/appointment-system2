from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Remove duplicate/empty Google OAuth apps, keeping only one'

    def handle(self, *args, **options):
        # Get all Google apps
        google_apps = SocialApp.objects.filter(provider='google')
        
        if google_apps.count() <= 1:
            self.stdout.write(
                self.style.SUCCESS('✓ No duplicates found. You have only one Google OAuth app.')
            )
            return
        
        self.stdout.write(f'Found {google_apps.count()} Google OAuth apps:')
        for i, app in enumerate(google_apps):
            self.stdout.write(f'  {i+1}. ID={app.id}, Name="{app.name}", Provider={app.provider}')
        
        # Keep the one with a non-empty name, delete others
        named_apps = [app for app in google_apps if app.name.strip()]
        unnamed_apps = [app for app in google_apps if not app.name.strip()]
        
        if not named_apps:
            # If no named app, keep the first one and delete the rest
            to_keep = google_apps[0]
            to_delete = google_apps[1:]
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ All Google OAuth apps are unnamed. Keeping ID={to_keep.id}, deleting others.'
                )
            )
        else:
            # Keep the named one, delete unnamed ones
            to_keep = named_apps[0]
            to_delete = unnamed_apps + named_apps[1:]
            self.stdout.write(
                self.style.SUCCESS(f'✓ Keeping: ID={to_keep.id}, Name="{to_keep.name}"')
            )
        
        if to_delete:
            count = len(to_delete)
            for app in to_delete:
                app.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deleted {count} duplicate Google OAuth app(s)')
            )
        
        self.stdout.write(
            self.style.SUCCESS('✓ Cleanup complete! Your register page should now work.')
        )

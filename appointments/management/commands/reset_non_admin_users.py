"""
Management command to delete all non-superuser accounts and clear Django sessions.

This command is intentionally destructive and therefore requires the
`--confirm` flag to run.

Usage:
    python manage.py reset_non_admin_users --confirm
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import transaction


class Command(BaseCommand):
    help = 'Delete all non-superuser accounts and clear active sessions without dropping database tables.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the deletion of non-superuser users and active sessions.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError(
                'This command is destructive. Add --confirm to proceed.'
            )

        with transaction.atomic():
            non_admin_qs = User.objects.filter(is_superuser=False)
            non_admin_count = non_admin_qs.count()

            if non_admin_count == 0:
                self.stdout.write(self.style.WARNING('No non-superuser users found.'))
            else:
                non_admin_qs.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {non_admin_count} non-superuser user(s).'
                    )
                )

            session_count = Session.objects.count()
            if session_count == 0:
                self.stdout.write(self.style.WARNING('No sessions found.'))
            else:
                Session.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {session_count} active session(s).'
                    )
                )

        self.stdout.write(self.style.NOTICE(
            'Completed cleanup. Admin/superuser accounts remain intact. Tables were not dropped.'
        ))

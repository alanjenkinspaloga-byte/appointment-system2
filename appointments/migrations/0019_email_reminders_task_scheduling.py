# Generated migration for email reminder and task scheduling fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0018_remove_appointment_google_calendar_event_id_and_more'),
    ]

    operations = [
        # Add email reminder scheduling fields to Appointment model
        migrations.AddField(
            model_name='appointment',
            name='reminder_interval_minutes',
            field=models.PositiveIntegerField(
                default=30,
                help_text='Minutes before appointment to send reminder email (default: 30 min)',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='reminder_sent_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp when reminder email was sent',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='scheduled_task_id',
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                help_text='Celery task ID for the scheduled reminder task',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='next_in_queue_notification_sent',
            field=models.BooleanField(
                default=False,
                help_text='Whether "you are next in queue" email has been sent',
            ),
        ),
    ]

# Generated migration for Google Calendar integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0012_contactmessage'),
    ]

    operations = [
        # Add Google Calendar fields to Doctor model
        migrations.AddField(
            model_name='doctor',
            name='is_google_calendar_connected',
            field=models.BooleanField(
                default=False,
                help_text='Whether the doctor has connected their Google Calendar account',
            ),
        ),
        migrations.AddField(
            model_name='doctor',
            name='google_calendar_token',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='Encrypted Google OAuth 2.0 token for calendar access',
            ),
        ),
        # Add Google Meet fields to Appointment model
        migrations.AddField(
            model_name='appointment',
            name='is_online_consultation',
            field=models.BooleanField(
                default=False,
                help_text='Whether this is an online consultation with Google Meet',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='google_meet_link',
            field=models.URLField(
                blank=True,
                null=True,
                help_text='Google Meet link for the online consultation',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='google_calendar_event_id',
            field=models.CharField(
                max_length=255,
                blank=True,
                null=True,
                help_text='Google Calendar event ID for this appointment',
            ),
        ),
    ]

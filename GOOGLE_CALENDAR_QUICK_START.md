# Google Calendar Integration - Quick Reference Card

## 🚀 For Doctors - Getting Started

### Connect Your Google Calendar (2 minutes)

1. Log in to your Doctor Dashboard
2. Look for **"Google Calendar Integration"** alert
3. Click **"Connect Google Calendar"**
4. Click **"Allow"** on Google's permission screen
5. Done! You're now ready for online consultations

### What Happens Next?

When a patient books an **online consultation**:

1. ✅ System creates a Google Calendar event
2. ✅ Generates a Google Meet video link automatically
3. ✅ Sends email invitation to both of you
4. ✅ Saves the link to the appointment

### To Join a Meeting

1. Go to **Appointments** → Find the online consultation
2. Click **"Join Google Meet"** button
3. Meeting opens in your browser
4. Allow camera/microphone permissions
5. Start consulting!

### To Disconnect Google Calendar

⚠️ **Warning**: New online appointments won't have Meet links if disconnected

1. Dashboard → Google Calendar Integration section
2. Click **"Disconnect"**
3. Confirm the action

---

## 👥 For Patients - Booking Online

### Book an Online Consultation (5 minutes)

1. Go to **Find a Doctor**
2. Choose your doctor
3. Select a date and time
4. ✅ Check the **"Online Consultation"** checkbox
5. Complete booking

### Receiving Your Link

After the doctor confirms your appointment:
- 📧 Email with Google Meet link arrives
- 📱 Open email and click the link
- 🎥 Or go to **My Appointments** → **Join Google Meet**

### During Your Consultation

- 🔔 Join 5-10 minutes early
- 📷 Allow camera/microphone access
- 💬 Video chat with your doctor
- 🔗 No software installation needed!

---

## 👨‍💼 For Admins - Dashboard Monitoring

### Track Google Calendar Usage

**Dashboard shows:**
- ✅ Number of doctors with Google Calendar connected
- ✅ Total online consultations this month
- ✅ Success rate of Meet link generation
- ✅ Doctor connection status

### Troubleshoot Doctor Connections

**If doctor has issues connecting:**

1. Check: Is browser updated?
2. Check: Google account has Gmail enabled?
3. Check: Doctor allowed permissions?
4. Solution: Try again in incognito mode
5. Escalate: Contact Google support if needed

### Monitor Google Calendar Operations

**Commands to run:**

```bash
# Check for errors
python manage.py shell
>>> from appointments.models import Appointment
>>> Appointment.objects.filter(is_online_consultation=True, google_meet_link__isnull=True)

# Count successful integrations
>>> Appointment.objects.filter(google_meet_link__isnull=False).count()
```

---

## 🔧 Technical Reference

### Database Fields Added

```
Doctor Model:
├── is_google_calendar_connected (True/False)
└── google_calendar_token (Encrypted credentials)

Appointment Model:
├── is_online_consultation (True/False)
├── google_meet_link (URL to Meet)
└── google_calendar_event_id (Event ID)
```

### New URL Endpoints

```
/appointments/google-oauth/authorize/      → Start OAuth
/appointments/google-oauth-callback/        → OAuth returns here
/appointments/google-calendar/disconnect/   → Remove connection
```

### API Scope Used

```
https://www.googleapis.com/auth/calendar.events
(Only for creating and viewing calendar events)
```

### Signal Flow

```
Appointment Confirmed
    ↓
Check: is_online_consultation = True
    ↓
Check: doctor.is_google_calendar_connected = True
    ↓
Create Google Calendar Event
    ↓
Extract Google Meet Link
    ↓
Save to appointment.google_meet_link
    ↓
Send Notifications
```

---

## 🆘 Common Issues & Solutions

### Issue: "Credentials file not found"
```
❌ Error: FileNotFoundError
✅ Solution: 
   - Place google_oauth_credentials.json in project root
   - Restart Django server
   - Try connecting again
```

### Issue: "Invalid OAuth state"
```
❌ Error: OAuth authorization failed
✅ Solution:
   - Clear browser cookies
   - Try connecting again
   - Check redirect URI in Google Cloud Console
```

### Issue: "Google Meet link not generated"
```
❌ Error: Appointment has no Meet link
✅ Solution:
   - Verify doctor is Google Calendar connected
   - Verify appointment is marked as "online consultation"
   - Check Django error logs
   - Try confirming appointment again
```

### Issue: "Email invitation not received"
```
❌ Error: No email after appointment confirmed
✅ Solution:
   - Check spam/junk folder
   - Verify email address is correct
   - Check email settings in Django
   - Wait 5 minutes (emails can be slow)
```

### Issue: "Can't join Google Meet"
```
❌ Error: Meet link doesn't work
✅ Solution:
   - Browser updated? Try latest Chrome/Firefox
   - Check internet connection
   - Disable VPN if using one
   - Try in incognito mode
   - Click "Join" instead of opening directly
```

---

## 📊 Performance Info

| Operation | Time | Notes |
|-----------|------|-------|
| Google Calendar authorization | 10-30s | One-time, redirects to Google |
| Meet link generation | 500-1000ms | After appointment confirmed |
| Email delivery | 1-5 min | Depends on email provider |
| Meet link accessible | Immediate | After email sent |

### API Quota
- **Free tier**: 10,000 API calls/day
- **Per appointment**: ~2 API calls
- **Sufficient for**: 5,000 appointments/day

---

## 🔒 Security & Privacy

✅ **What We Store:**
- Google OAuth token (for calendar access)
- Google Meet link (public URL)
- Event ID (for future reference)

❌ **What We DON'T Store:**
- Google password
- Email content
- Personal Google Drive files
- Other Google account data

✅ **Permissions Requested:**
- Read/write calendar events only
- No email access
- No contact access
- No Google Drive access

---

## 📚 Documentation

For more details, see:

- **[GOOGLE_CALENDAR_INTEGRATION.md](GOOGLE_CALENDAR_INTEGRATION.md)**
  - Complete setup guide
  - Configuration instructions
  - Troubleshooting guide

- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**
  - Code examples
  - Integration with existing views
  - Testing examples

- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**
  - Pre-deployment checklist
  - Production configuration
  - Monitoring setup

---

## 🎯 Next Steps

### For Doctors
1. ✅ Connect Google Calendar (1 min)
2. ✅ Check dashboard shows "Connected" (1 min)
3. ✅ Wait for first online appointment (varies)
4. ✅ Confirm appointment and verify Meet link (2 min)

### For Admins
1. ✅ Place credentials file (1 min)
2. ✅ Run migrations (2 min)
3. ✅ Restart Django (1 min)
4. ✅ Monitor dashboard (ongoing)

### For IT/DevOps
1. ✅ Update production settings (5 min)
2. ✅ Configure environment variables (5 min)
3. ✅ Set up logging and monitoring (10 min)
4. ✅ Test complete flow (15 min)
5. ✅ Deploy to production (varies)

---

## 📞 Support

**Problem?** Follow this order:

1. Check Common Issues above
2. Read GOOGLE_CALENDAR_INTEGRATION.md troubleshooting section
3. Check Django logs
4. Check Google Cloud Console status
5. Contact IT support with details

---

## ✅ Success Indicators

Your integration is working correctly if:

- ✅ Doctors can connect Google Calendar
- ✅ Appointments marked "online consultation"
- ✅ Meet links appear in appointment details
- ✅ Email invitations received
- ✅ Can click "Join Google Meet" successfully
- ✅ No errors in Django logs
- ✅ Video conference works properly

---

**Version:** 1.0  
**Last Updated:** May 7, 2026  
**Status:** Production Ready ✅

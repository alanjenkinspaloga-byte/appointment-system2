# Time Slot Booking System - Implementation Guide

## Overview

This document describes the minute-by-minute time slot booking system that constrains all appointments within doctor-defined availability windows.

---

## Features Implemented

### 1. **Doctor-Defined Availability Windows**
- Doctors create availability slots with specific `start_time` and `end_time`
- Example: 9:00 AM to 12:00 PM at Hospital A
- Each availability slot can be at a different location (hospital/clinic)
- Doctors can pause availability to stop accepting patients

### 2. **Minute-by-Minute Time Slots**
- Time slots are generated automatically from `start_time` to `end_time` (every minute)
- Example: 9:00, 9:01, 9:02, ..., 11:59
- Each time slot is unique per doctor per date (database constraint)
- Patients can only select times within the availability window

### 3. **Booked Slot Management**
- Once a patient books a time, it's immediately unavailable for others
- Database constraint: `unique_together = ('doctor', 'date', 'appointment_time')`
- Prevents double-booking via IntegrityError exception handling
- Multiple doctors have independent slot reservations

### 4. **Patient-Friendly UI**
- Interactive time picker showing:
  - Available times (green buttons)
  - Already booked times (red buttons)
  - Availability window info
  - Real-time slot count and progress bar
- Only free times are clickable
- Clear error messages if slot is unavailable

---

## Database Schema Changes

### Appointment Model Changes

```python
class Appointment(models.Model):
    # ... existing fields ...
    
    # New field - specific appointment time (minute-by-minute)
    appointment_time = models.TimeField(
        blank=True, null=True,
        help_text='Specific time slot for the appointment (minute-by-minute)'
    )
    
    # ... rest of fields ...
    
    class Meta:
        ordering = ['date', 'appointment_time']
        # CONSTRAINT: Ensure each doctor can only have ONE appointment per time per day
        unique_together = ('doctor', 'date', 'appointment_time')
```

### Key Constraints

1. **Uniqueness**: `unique_together = ('doctor', 'date', 'appointment_time')`
   - Prevents same doctor from having multiple patients at the same minute
   - Different doctors can have the same time (independent queues)

2. **Availability Window Enforcement**:
   - View validates: `start_time <= appointment_time < end_time`
   - Only times within window are shown to patients
   - Server-side validation prevents booking outside window

3. **Doctor-Specific Queue**:
   - Queue numbers calculated using `appointment_time`
   - Each doctor maintains their own queue independently

---

## File Structure Changes

### New Files Created

```
appointments/templatetags/
  ├── __init__.py
  └── math_filters.py         # Custom template filters for math operations
```

### Modified Files

```
appointments/
  ├── models.py               # Added appointment_time field
  ├── forms.py                # Added appointment_time to booking form
  ├── views.py                # Enhanced BookAppointmentView
  │
  migrations/
  └── 0011_*.py               # Migration for new field
  
templates/patient/
  └── book_appointment.html   # New time picker widget
```

---

## Core Components

### 1. View Logic - `BookAppointmentView`

#### Method: `_get_available_times(availability)`
```python
def _get_available_times(self, availability):
    """
    Generate minute-by-minute time slots between availability start and end time.
    CONSTRAINT: Only times between availability.start_time and availability.end_time
    
    Returns: List of time objects at 1-minute intervals
    
    Example:
        Availability: 9:00 AM - 12:00 PM
        Returns: [09:00, 09:01, 09:02, ..., 11:59]
    """
```

#### Method: `_get_booked_times(doctor, appointment_date)`
```python
def _get_booked_times(self, doctor, appointment_date):
    """
    Get all booked times for a doctor on a specific date.
    Only includes appointments with status: pending, confirmed, in_progress
    
    Returns: Set of reserved appointment_time values
    """
```

#### GET Handler
1. Validates availability slot exists and is accepting patients
2. Generates all possible times within window
3. Queries database for booked times
4. Filters out booked times
5. Shows available times to patient

#### POST Handler
1. Retrieves selected appointment_time
2. Validates time is still available (race-condition safe)
3. Validates time is within availability window
4. Saves appointment with unique constraint enforcement
5. Handles IntegrityError if time was just taken

---

## Validation Layers

### Layer 1: Frontend Validation (JavaScript)
- Only available times are clickable buttons
- Submit button disabled until time selected
- Visual indicators (green/red) show slot status

### Layer 2: Form Validation (Django Form)
- TimeField validation
- Hour/Minute format checking

### Layer 3: View Validation (BookAppointmentView)
- Time within availability window: `start_time <= time < end_time`
- Time not already booked: Check booked_times set
- Patient not already booked at this time (former check - now via unique constraint)

### Layer 4: Database Validation (Unique Constraint)
- Unique constraint on (doctor, date, appointment_time)
- IntegrityError raised if violated
- Second line of defense against race conditions

---

## Context Data Passed to Template

```python
{
    'form': AppointmentBookingForm(),
    'availability': Availability object,
    'available_times': [09:00, 09:01, 09:02, ...],  # Times within window, not booked
    'booked_times': [10:30, 11:45, ...],            # Times within window that are booked
    'total_slots': 180,                              # Total minutes in window
    'booked_count': 5,                               # Number of booked slots
    'free_count': 175,                               # Number of free slots
}
```

---

## Template Features (book_appointment.html)

### 1. Appointment Details Card
- Shows doctor info
- Display availability window times
- Shows location (hospital/clinic)
- Shows fees

### 2. Slot Availability Summary
- Real-time count of available vs booked
- Progress bar showing utilization
- Time window reminder

### 3. Time Slot Picker
- **Available Times Grid**: Green buttons for all free times
  - Only times within window are shown
  - Only unbooked times are shown
  - User clicks to select
- **Booked Times Grid**: Red buttons for reference
  - Shows what times are taken
  - Cannot be clicked (disabled)
  - Greyed out for visual clarity

### 4. Booking Form
- Displays selected time with badges
- Reason for visit textarea
- Confirm button (enabled only after time selected)
- Visual feedback on submission

### 5. Custom Template Filters
- `@register.filter def add()` - Addition
- `@register.filter name='mul'` - Multiplication  
- `@register.filter name='divideby'` - Division
- `@register.filter def percentage()` - Percentage calculation
- Used for progress bar calculations

---

## Error Handling & Messages

### Scenario: Slot Already Booked
```
❌ "Time 10:30 is already booked. Please select another time."
Action: Re-render form with updated available times
```

### Scenario: Time Outside Availability
```
❌ "Selected time is outside available hours."
Action: Re-render form - shouldn't occur if UI is working correctly
```

### Scenario: Slot Taken During Booking (Race Condition)
```
❌ "Time 10:30 is already used. If you just booked it, it may have been 
   taken by another patient. Please try a different time."
Action: IntegrityError caught and handled gracefully
```

### Scenario: Availability Paused
```
⚠️ "This schedule slot is currently paused."
Action: Redirect to doctor schedule
```

### Scenario: All Slots Booked
```
⚠️ "All time slots are fully booked for this availability."
Action: Redirect to doctor schedule
```

---

## Time Slot Calculation Example

### Input
```
Availability:
  - Start: 09:00
  - End: 09:05 (5 minute window for demo)
  - Date: 2026-05-04
  
Already Booked: 09:02, 09:04
```

### Output
```
Available Times Grid (clickable):
  - 09:00 ✓ Green
  - 09:01 ✓ Green
  - 09:03 ✓ Green

Booked Times Grid (disabled):
  - 09:02 ✗ Red
  - 09:04 ✗ Red

Total Slots: 5
Free Count: 3
Booked Count: 2
```

---

## Doctor Queue Numbering

Queue numbers are assigned based on appointment time, ensuring chronological order:

```
Doctor A on May 4, 2026:
  Patient X booked at 09:00 → Queue #1 (earliest)
  Patient Y booked at 10:30 → Queue #2
  Patient Z booked at 09:15 → Queue #2 (shifted), Patient Y becomes #3

The system automatically renumbers based on appointment_time.
```

---

## Testing Checklist

### Basic Functionality
- [ ] Create doctor with availability slot (9:00-12:00)
- [ ] As patient, view doctor's schedule
- [ ] See all available times from 9:00-11:59
- [ ] Book a time (e.g., 9:30)
- [ ] Verify 9:30 now appears as booked (red)
- [ ] Attempt to book 9:30 again → See error message
- [ ] Book different time successfully

### Availability Window Enforcement
- [ ] Create availability 9:00-12:00
- [ ] Verify times 8:59 and 12:00 are NOT shown
- [ ] Verify times 9:00 and 11:59 ARE shown
- [ ] Manually try to POST time outside window → Error

### Multiple Doctors
- [ ] Create Doctor A (9:00-12:00) and Doctor B (10:00-13:00)
- [ ] Book time with Doctor A (9:30)
- [ ] Book same time with Doctor B (9:30) - should work (different doctors)
- [ ] Doctor A queue should have Patient at 9:30
- [ ] Doctor B queue should have different Patient at 9:30

### Race Conditions
- [ ] Open booking page twice
- [ ] Book same time in both windows
- [ ] First succeeds, second shows: "Time already used"
- [ ] Verify database only has one record (unique constraint)

### UI/UX
- [ ] Submit button disabled until time selected
- [ ] Time display updates when slot clicked
- [ ] Booked times clearly marked in red
- [ ] Available times clearly marked in green
- [ ] Window shows progress bar with accurate counts

---

## Future Enhancements

1. **Slot Duration**: Instead of 1-minute slots, allow configurable duration (15, 30, 60 min)
2. **Buffer Time**: Add gap between appointments
3. **Recurring Availability**: Let doctors set recurring schedules
4. **Calendar View**: Show availability graphically
5. **Time Filters**: Filter slots by duration, location, etc.
6. **Notifications**: Alert patients when slots in their window open
7. **Rebooking**: Allow patients to reschedule to different times

---

## Support & Troubleshooting

### Issue: Template Filter Not Recognized
**Solution**: Restart Django development server
```bash
python manage.py runserver
```

### Issue: Times Outside Window Appearing
**Solution**: Check `_get_available_times()` logic - verify start_time < end_time

### Issue: Booked Times Not Showing as Red
**Solution**: Verify `booked_times` is being passed to template context

### Issue: Cannot Book Any Slot
**Solution**: Check availability `accepting_status` isn't set to 'paused'

---

## Code References

- **Model**: `appointments/models.py` - Lines ~290-350
- **View**: `appointments/views.py` - `BookAppointmentView` class
- **Form**: `appointments/forms.py` - `AppointmentBookingForm`
- **Template**: `templates/patient/book_appointment.html`
- **Filters**: `appointments/templatetags/math_filters.py`
- **Migration**: `appointments/migrations/0011_*.py`

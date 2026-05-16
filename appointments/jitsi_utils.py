# ============================================================
# appointments/jitsi_utils.py
# Jitsi Meet Integration Utilities
# ============================================================
"""
Utilities for generating and managing Jitsi Meet URLs for online consultations.
"""

import uuid
import logging

logger = logging.getLogger(__name__)

JITSI_SERVER = 'https://meet.jit.si'


def generate_jitsi_meet_link(doctor_id, patient_id, appointment_id):
    """
    Generate a unique Jitsi Meet URL for an online consultation.
    
    Args:
        doctor_id: ID of the doctor
        patient_id: ID of the patient
        appointment_id: ID of the appointment
        
    Returns:
        Full Jitsi Meet URL (string)
    
    Example:
        generate_jitsi_meet_link(5, 12, 42) 
        -> https://meet.jit.si/okidoki-5-12-42-a7c3d9e2
    """
    # Generate a short random slug for additional uniqueness
    random_slug = str(uuid.uuid4())[:8]
    
    # Create room name (lowercase, hyphens instead of underscores for Jitsi compatibility)
    room_name = f"okidoki-{doctor_id}-{patient_id}-{appointment_id}-{random_slug}"
    
    # Construct full URL
    jitsi_url = f"{JITSI_SERVER}/{room_name}"
    
    logger.info(f"Generated Jitsi Meet link for appointment {appointment_id}: {jitsi_url}")
    
    return jitsi_url

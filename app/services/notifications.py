import logging
from flask import current_app
from app.auth.models import AuthUser
from app.seed import schema
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import GetRecordRequest
from app.modules.routes_base import _ctx

def notify_lab_result(test_data, test_id):
    """Simulate sending a lab result report to doctor and admin."""
    doctor_lookup = test_data.get("doctor_lookup")
    patient_lookup = test_data.get("patient_lookup")
    
    # Get doctor email
    doctor = AuthUser.query.filter_by(hogc_record_id=doctor_lookup).first() if doctor_lookup else None
    doctor_email = doctor.email if doctor else None
    
    # Get admin emails
    admins = AuthUser.query.filter_by(role="Admin").all()
    admin_emails = [admin.email for admin in admins if admin.email]
    
    # Get patient details for the report
    patient_name = "Unknown Patient"
    if patient_lookup:
        try:
            p_resp = HOGC.crud.record.get(GetRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, record_id=patient_lookup))
            if p_resp.data:
                patient_name = f"{p_resp.data.data.get('first_name', '')} {p_resp.data.data.get('last_name', '')}"
        except Exception:
            pass
            
    recipients = []
    if doctor_email:
        recipients.append(doctor_email)
    recipients.extend(admin_emails)
    
    # Remove duplicates
    recipients = list(set(recipients))
    
    if not recipients:
        return []
        
    test_name = test_data.get("test_name", "Unknown Test")
    result_val = test_data.get("result_value", "N/A")
    ref_range = test_data.get("reference_range", "N/A")
    
    report_body = f"""
=========================================
LABORATORY RESULT REPORT
=========================================
Test ID: LAB-{test_id[:8].upper()}
Test Name: {test_name}
Patient: {patient_name}
Status: Completed

Result Value: 
{result_val}

Reference Range: {ref_range}
=========================================
    """
    
    current_app.logger.info(f"Sending Lab Result Report to: {', '.join(recipients)}")
    current_app.logger.info(report_body)
    
    return recipients

"""Seed data — Default admin user and sample records."""
from hogc.lib import HOGC
from app.extensions import db
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest
from app.config import Config


def _ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_default_admin(module_id):
    from app.auth.models import AuthUser
    admin = AuthUser.query.filter_by(username="admin").first()
    if not admin:
        admin = AuthUser(
            username="admin",
            email="admin@hospital.com",
            full_name="System Admin",
            role="Admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        try:
            ctx = _ctx()
            record = HOGC.crud.record.create(CreateRecordRequest(
                context=ctx,
                module_id=module_id,
                data={
                    "full_name": "System Admin",
                    "email": "admin@hospital.com",
                    "role": "Admin",
                    "is_active": "true",
                },
            ))
            admin.hogc_record_id = record.data.id
            db.session.commit()
        except Exception:
            pass


def _seed_default_data(module_ids):
    """Create sample records across all modules."""
    ctx = _ctx()
    users_id = module_ids["users"]
    patients_id = module_ids["patients"]
    visits_id = module_ids["visits"]
    inventory_id = module_ids["inventory"]
    prescriptions_id = module_ids["prescriptions"]
    laboratory_id = module_ids["laboratory"]

    # Doctors / Staff
    from app.auth.models import AuthUser

    staff_data = [
        {"full_name": "Dr. Sarah Johnson", "email": "sarah.johnson@hospital.com",
         "phone": "+1-555-0101", "role": "Doctor", "department": "Cardiology", "is_active": "true",
         "username": "sarah.johnson", "password": "password123"},
        {"full_name": "Dr. James Patel", "email": "james.patel@hospital.com",
         "phone": "+1-555-0102", "role": "Doctor", "department": "Neurology", "is_active": "true",
         "username": "james.patel", "password": "password123"},
        {"full_name": "Dr. Emily Chen", "email": "emily.chen@hospital.com",
         "phone": "+1-555-0103", "role": "Doctor", "department": "Pediatrics", "is_active": "true",
         "username": "emily.chen", "password": "password123"},
        {"full_name": "Dr. Robert Williams", "email": "robert.williams@hospital.com",
         "phone": "+1-555-0104", "role": "Doctor", "department": "Orthopedics", "is_active": "true",
         "username": "robert.williams", "password": "password123"},
        {"full_name": "Linda Davis", "email": "linda.davis@hospital.com",
         "phone": "+1-555-0105", "role": "Nurse", "department": "General", "is_active": "true",
         "username": "linda.davis", "password": "password123"},
    ]

    doctor_ids = []
    for s in staff_data:
        username = s.pop("username")
        password = s.pop("password")
        auth_user = AuthUser(username=username, email=s["email"],
                             full_name=s["full_name"], role=s["role"])
        auth_user.set_password(password)
        db.session.add(auth_user)
        db.session.commit()
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=users_id, data=s
        ))
        auth_user.hogc_record_id = resp.data.id
        db.session.commit()
        doctor_ids.append(resp.data.id)

    # Patients
    patients_data = [
        {"first_name": "Rajesh", "last_name": "Kumar", "date_of_birth": "1985-03-15",
         "gender": "Male", "phone": "+91-9876543210", "email": "rajesh.kumar@email.com",
         "address": "12 MG Road, Bangalore 560001", "blood_group": "B+",
         "emergency_contact": "Priya Kumar", "emergency_phone": "+91-9876543211",
         "insurance_provider": "Star Health", "insurance_id": "SH-2024-001",
         "medical_history": "Hypertension", "allergies": "Penicillin", "status": "Active"},
        {"first_name": "Ananya", "last_name": "Sharma", "date_of_birth": "1992-07-22",
         "gender": "Female", "phone": "+91-9876543220", "email": "ananya.sharma@email.com",
         "address": "45 Park Street, Kolkata 700016", "blood_group": "O+",
         "emergency_contact": "Vikram Sharma", "emergency_phone": "+91-9876543221",
         "insurance_provider": "ICICI Lombard", "insurance_id": "IL-2024-042",
         "medical_history": "None", "allergies": "None", "status": "Active"},
        {"first_name": "Mohammed", "last_name": "Ali", "date_of_birth": "1978-11-08",
         "gender": "Male", "phone": "+91-9876543230", "email": "mohammed.ali@email.com",
         "address": "78 Jubilee Hills, Hyderabad 500033", "blood_group": "A+",
         "emergency_contact": "Fatima Ali", "emergency_phone": "+91-9876543231",
         "insurance_provider": "Max Bupa", "insurance_id": "MB-2024-118",
         "medical_history": "Diabetes Type 2", "allergies": "Sulfa drugs", "status": "Active"},
        {"first_name": "Priya", "last_name": "Nair", "date_of_birth": "1990-01-30",
         "gender": "Female", "phone": "+91-9876543240", "email": "priya.nair@email.com",
         "address": "23 Marine Drive, Kochi 682001", "blood_group": "AB+",
         "emergency_contact": "Suresh Nair", "emergency_phone": "+91-9876543241",
         "insurance_provider": "Star Health", "insurance_id": "SH-2024-055",
         "medical_history": "Asthma", "allergies": "Dust, Pollen", "status": "Active"},
        {"first_name": "Arjun", "last_name": "Reddy", "date_of_birth": "1988-05-12",
         "gender": "Male", "phone": "+91-9876543250", "email": "arjun.reddy@email.com",
         "address": "56 Banjara Hills, Hyderabad 500034", "blood_group": "O-",
         "emergency_contact": "Lakshmi Reddy", "emergency_phone": "+91-9876543251",
         "insurance_provider": "HDFC Ergo", "insurance_id": "HE-2024-203",
         "medical_history": "None", "allergies": "None", "status": "Active"},
        {"first_name": "Deepa", "last_name": "Menon", "date_of_birth": "1975-09-18",
         "gender": "Female", "phone": "+91-9876543260", "email": "deepa.menon@email.com",
         "address": "89 Indiranagar, Bangalore 560038", "blood_group": "A-",
         "emergency_contact": "Ravi Menon", "emergency_phone": "+91-9876543261",
         "insurance_provider": "Bajaj Allianz", "insurance_id": "BA-2024-077",
         "medical_history": "Thyroid disorder, Arthritis", "allergies": "Aspirin", "status": "Active"},
        {"first_name": "Vikram", "last_name": "Singh", "date_of_birth": "1995-12-05",
         "gender": "Male", "phone": "+91-9876543270", "email": "vikram.singh@email.com",
         "address": "34 Connaught Place, New Delhi 110001", "blood_group": "B-",
         "emergency_contact": "Meera Singh", "emergency_phone": "+91-9876543271",
         "insurance_provider": "ICICI Lombard", "insurance_id": "IL-2024-156",
         "medical_history": "None", "allergies": "None", "status": "Active"},
        {"first_name": "Kavitha", "last_name": "Iyer", "date_of_birth": "1982-06-25",
         "gender": "Female", "phone": "+91-9876543280", "email": "kavitha.iyer@email.com",
         "address": "67 T Nagar, Chennai 600017", "blood_group": "AB-",
         "emergency_contact": "Ramesh Iyer", "emergency_phone": "+91-9876543281",
         "insurance_provider": "Max Bupa", "insurance_id": "MB-2024-089",
         "medical_history": "Migraine", "allergies": "Ibuprofen", "status": "Active"},
    ]

    patient_ids = []
    for p in patients_data:
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=patients_id, data=p
        ))
        patient_ids.append(resp.data.id)

    # Inventory
    inventory_data = [
        {"item_name": "Paracetamol 500mg", "category": "Medication", "description": "Fever and pain relief tablets",
         "quantity": "500", "unit": "Strip", "unit_price": "25.00", "supplier": "Cipla Ltd",
         "reorder_level": "100", "expiry_date": "2027-06-30", "batch_number": "PCM-2026-A1",
         "location": "Pharmacy Store A", "status": "In-Stock"},
        {"item_name": "Amoxicillin 250mg", "category": "Medication", "description": "Broad-spectrum antibiotic capsules",
         "quantity": "200", "unit": "Strip", "unit_price": "45.00", "supplier": "Sun Pharma",
         "reorder_level": "50", "expiry_date": "2027-03-15", "batch_number": "AMX-2026-B3",
         "location": "Pharmacy Store A", "status": "In-Stock"},
        {"item_name": "Surgical Gloves (Medium)", "category": "Consumable", "description": "Latex-free sterile surgical gloves",
         "quantity": "50", "unit": "Box", "unit_price": "350.00", "supplier": "MedLine Industries",
         "reorder_level": "20", "expiry_date": "2028-12-31", "batch_number": "SG-2026-M1",
         "location": "Central Store", "status": "In-Stock"},
        {"item_name": "Digital Thermometer", "category": "Equipment", "description": "Clinical digital thermometer with memory",
         "quantity": "15", "unit": "Piece", "unit_price": "450.00", "supplier": "Omron Healthcare",
         "reorder_level": "5", "expiry_date": "", "batch_number": "DT-2026-01",
         "location": "Ward Supply Room", "status": "In-Stock"},
        {"item_name": "Insulin Glargine 100IU/ml", "category": "Medication", "description": "Long-acting insulin for diabetes management",
         "quantity": "30", "unit": "Vial", "unit_price": "1200.00", "supplier": "Sanofi India",
         "reorder_level": "10", "expiry_date": "2027-01-20", "batch_number": "INS-2026-G5",
         "location": "Cold Storage", "status": "In-Stock"},
    ]

    for item in inventory_data:
        HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=inventory_id, data=item
        ))

    # Visits
    visits_data = [
        {"patient_lookup": patient_ids[0], "doctor_lookup": doctor_ids[0],
         "visit_date": "2026-07-15T09:00", "department": "Cardiology",
         "chief_complaint": "Chest pain and shortness of breath",
         "diagnosis": "Mild angina pectoris", "treatment": "Prescribed nitrates and lifestyle modification",
         "vitals_bp": "150/95", "vitals_temp": "98.4F", "vitals_pulse": "88 bpm",
         "vitals_weight": "78 kg", "status": "Completed", "notes": "Follow-up in 2 weeks"},
        {"patient_lookup": patient_ids[1], "doctor_lookup": doctor_ids[2],
         "visit_date": "2026-07-16T10:30", "department": "General",
         "chief_complaint": "Persistent cough and fever for 3 days",
         "diagnosis": "Upper respiratory tract infection", "treatment": "Antibiotics and rest",
         "vitals_bp": "120/80", "vitals_temp": "101.2F", "vitals_pulse": "76 bpm",
         "vitals_weight": "55 kg", "status": "Completed", "notes": "Viral etiology suspected"},
        {"patient_lookup": patient_ids[2], "doctor_lookup": doctor_ids[0],
         "visit_date": "2026-07-17T11:00", "department": "Cardiology",
         "chief_complaint": "Routine diabetes checkup and blood sugar monitoring",
         "diagnosis": "Diabetes Type 2 - controlled", "treatment": "Continue current medication",
         "vitals_bp": "130/85", "vitals_temp": "98.6F", "vitals_pulse": "72 bpm",
         "vitals_weight": "82 kg", "status": "Completed", "notes": "HbA1c test ordered"},
        {"patient_lookup": patient_ids[3], "doctor_lookup": doctor_ids[1],
         "visit_date": "2026-07-18T14:00", "department": "Neurology",
         "chief_complaint": "Recurring severe headaches with visual aura",
         "diagnosis": "Migraine with aura", "treatment": "Triptans prescribed, MRI recommended",
         "vitals_bp": "118/76", "vitals_temp": "98.2F", "vitals_pulse": "68 bpm",
         "vitals_weight": "62 kg", "status": "Completed", "notes": "MRI scheduled for next week"},
        {"patient_lookup": patient_ids[4], "doctor_lookup": doctor_ids[3],
         "visit_date": "2026-07-19T09:30", "department": "Orthopedics",
         "chief_complaint": "Lower back pain radiating to left leg",
         "diagnosis": "", "treatment": "",
         "vitals_bp": "125/82", "vitals_temp": "98.6F", "vitals_pulse": "74 bpm",
         "vitals_weight": "75 kg", "status": "In-Progress", "notes": "X-ray ordered"},
    ]

    visit_ids = []
    for v in visits_data:
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=visits_id, data=v
        ))
        visit_ids.append(resp.data.id)

    # Prescriptions
    prescriptions_data = [
        {"patient_lookup": patient_ids[0], "doctor_lookup": doctor_ids[0],
         "visit_lookup": visit_ids[0], "prescribed_date": "2026-07-15",
         "medication_name": "Isosorbide Mononitrate 20mg", "dosage": "20mg",
         "frequency": "Twice daily", "duration": "30 days",
         "instructions": "Take after meals. Avoid sudden position changes.",
         "refills": "2", "status": "Active"},
        {"patient_lookup": patient_ids[1], "doctor_lookup": doctor_ids[2],
         "visit_lookup": visit_ids[1], "prescribed_date": "2026-07-16",
         "medication_name": "Amoxicillin 250mg", "dosage": "250mg",
         "frequency": "Three times daily", "duration": "7 days",
         "instructions": "Complete the full course. Take with water.",
         "refills": "0", "status": "Active"},
        {"patient_lookup": patient_ids[2], "doctor_lookup": doctor_ids[0],
         "visit_lookup": visit_ids[2], "prescribed_date": "2026-07-17",
         "medication_name": "Metformin 500mg", "dosage": "500mg",
         "frequency": "Twice daily", "duration": "90 days",
         "instructions": "Take with meals to reduce GI side effects.",
         "refills": "3", "status": "Active"},
    ]

    for rx in prescriptions_data:
        HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=prescriptions_id, data=rx
        ))

    # Laboratory Tests
    lab_data = [
        {"patient_lookup": patient_ids[2], "doctor_lookup": doctor_ids[0],
         "visit_lookup": visit_ids[2], "test_name": "HbA1c (Glycated Hemoglobin)",
         "test_type": "Blood", "priority": "Routine", "sample_date": "2026-07-17T11:30",
         "result_date": "2026-07-18T09:00", "result_value": "6.8%",
         "reference_range": "4.0 - 5.6% (Normal), 5.7 - 6.4% (Pre-diabetes)",
         "status": "Completed", "notes": "Slightly elevated, consistent with controlled diabetes",
         "technician_lookup": doctor_ids[4]},
        {"patient_lookup": patient_ids[1], "doctor_lookup": doctor_ids[2],
         "visit_lookup": visit_ids[1], "test_name": "Complete Blood Count (CBC)",
         "test_type": "Blood", "priority": "Routine", "sample_date": "2026-07-16T11:00",
         "result_date": "2026-07-16T16:00",
         "result_value": "WBC: 11,200/uL, RBC: 4.5M/uL, Hgb: 13.2 g/dL, Platelets: 250K/uL",
         "reference_range": "WBC: 4,500-11,000/uL, RBC: 4.0-5.5M/uL",
         "status": "Completed", "notes": "Mildly elevated WBC consistent with infection",
         "technician_lookup": doctor_ids[4]},
        {"patient_lookup": patient_ids[4], "doctor_lookup": doctor_ids[3],
         "visit_lookup": visit_ids[4], "test_name": "Lumbar Spine X-Ray",
         "test_type": "X-Ray", "priority": "Urgent", "sample_date": "2026-07-19T10:00",
         "result_date": "", "result_value": "",
         "reference_range": "", "status": "Ordered",
         "notes": "Suspected disc herniation",
         "technician_lookup": ""},
    ]

    for lab in lab_data:
        HOGC.crud.record.create(CreateRecordRequest(
            context=ctx, module_id=laboratory_id, data=lab
        ))

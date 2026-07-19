import uuid
from flask import current_app
from app.extensions import crud, SessionLocal, db
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateModuleRequest, CreateFieldRequest, AddPicklistOptionRequest,
    ListModulesRequest, CreateRecordRequest,
)
from hogc.lib.contracts.crud.types import FieldType

# Module IDs - set after creation
USERS_MODULE_ID = None
PATIENTS_MODULE_ID = None
VISITS_MODULE_ID = None
INVENTORY_MODULE_ID = None
PRESCRIPTIONS_MODULE_ID = None
LABORATORY_MODULE_ID = None

# Field name -> ID mapping for picklist options
_field_ids = {}


def _ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_module(name, api_name, label, plural_label, description=""):
    resp = crud.modules.create_module(CreateModuleRequest(
        context=_ctx(),
        name=name,
        api_name=api_name,
        label=label,
        plural_label=plural_label,
        description=description,
    ))
    return resp.data.id


def _create_field(module_id, field_name, api_name, field_type, label="",
                  is_required=False, is_unique=False, default_value=None,
                  lookup_module_id=None):
    resp = crud.fields.create_field(CreateFieldRequest(
        context=_ctx(),
        module_id=module_id,
        field_name=field_name,
        api_name=api_name,
        field_type=field_type,
        label=label or field_name,
        is_required=is_required,
        is_unique=is_unique,
        default_value=default_value,
        lookup_module_id=lookup_module_id,
    ))
    _field_ids[api_name] = resp.data.id
    return resp.data.id


def _add_picklist(field_id, value, label, color=None, is_default=False, order=0):
    crud.picklists.add_option(AddPicklistOptionRequest(
        context=_ctx(),
        field_id=field_id,
        value=value,
        label=label,
        color=color,
        is_default=is_default,
        display_order=order,
    ))


def _create_relationship(from_module_id, to_module_id, rel_type, from_field="", to_field=""):
    session = SessionLocal()
    try:
        rel_id = uuid.uuid4().hex
        session.execute(db.text("""
            INSERT INTO relationship_definitions
            (id, tenant_id, org_id, created_at, updated_at, created_by, updated_by,
             version, status, tags_json, metadata_json,
             from_module_id, to_module_id, relationship_type,
             from_field_name, to_field_name, cascade_delete)
            VALUES
            (:id, :tenant_id, :org_id, NOW(), NOW(), 'system', 'system',
             1, 'active', '[]', '{}',
             :from_module_id, :to_module_id, :rel_type,
             :from_field, :to_field, false)
        """), {
            "id": rel_id,
            "tenant_id": Config.HOGC_TENANT_ID,
            "org_id": Config.HOGC_ORG_ID,
            "from_module_id": from_module_id,
            "to_module_id": to_module_id,
            "rel_type": rel_type,
            "from_field": from_field,
            "to_field": to_field,
        })
        session.commit()
        return rel_id
    except Exception:
        session.rollback()
        return None
    finally:
        session.close()


def _seed_users_module():
    global USERS_MODULE_ID
    USERS_MODULE_ID = _create_module("users", "users", "User", "Users", "Hospital staff and users")
    _create_field(USERS_MODULE_ID, "Full Name", "full_name", FieldType.TEXT, "Full Name", is_required=True)
    _create_field(USERS_MODULE_ID, "Email", "email", FieldType.EMAIL, "Email", is_required=True)
    _create_field(USERS_MODULE_ID, "Phone", "phone", FieldType.PHONE, "Phone")
    role_id = _create_field(USERS_MODULE_ID, "Role", "role", FieldType.PICKLIST, "Role", is_required=True)
    for i, (val, lbl) in enumerate([("Admin", "Admin"), ("Doctor", "Doctor"), ("Nurse", "Nurse"),
                                     ("Pharmacist", "Pharmacist"), ("Lab Technician", "Lab Technician")]):
        _add_picklist(role_id, val, lbl, is_default=(i == 1), order=i)
    _create_field(USERS_MODULE_ID, "Department", "department", FieldType.TEXT, "Department")
    _create_field(USERS_MODULE_ID, "Is Active", "is_active", FieldType.BOOLEAN, "Is Active", default_value="true")


def _seed_patients_module():
    global PATIENTS_MODULE_ID
    PATIENTS_MODULE_ID = _create_module("patients", "patients", "Patient", "Patients", "Patient records")
    _create_field(PATIENTS_MODULE_ID, "Patient ID", "patient_id", FieldType.AUTO_NUMBER, "Patient ID", is_unique=True)
    _create_field(PATIENTS_MODULE_ID, "First Name", "first_name", FieldType.TEXT, "First Name", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Last Name", "last_name", FieldType.TEXT, "Last Name", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Date of Birth", "date_of_birth", FieldType.DATE, "Date of Birth", is_required=True)
    gender_id = _create_field(PATIENTS_MODULE_ID, "Gender", "gender", FieldType.PICKLIST, "Gender", is_required=True)
    for i, (val, lbl) in enumerate([("Male", "Male"), ("Female", "Female"), ("Other", "Other")]):
        _add_picklist(gender_id, val, lbl, order=i)
    _create_field(PATIENTS_MODULE_ID, "Phone", "phone", FieldType.PHONE, "Phone", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Email", "email", FieldType.EMAIL, "Email")
    _create_field(PATIENTS_MODULE_ID, "Address", "address", FieldType.TEXT, "Address")
    bg_id = _create_field(PATIENTS_MODULE_ID, "Blood Group", "blood_group", FieldType.PICKLIST, "Blood Group")
    for i, (val, lbl) in enumerate([("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
                                     ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-")]):
        _add_picklist(bg_id, val, lbl, order=i)
    _create_field(PATIENTS_MODULE_ID, "Emergency Contact", "emergency_contact", FieldType.TEXT, "Emergency Contact")
    _create_field(PATIENTS_MODULE_ID, "Emergency Phone", "emergency_phone", FieldType.PHONE, "Emergency Phone")
    _create_field(PATIENTS_MODULE_ID, "Insurance Provider", "insurance_provider", FieldType.TEXT, "Insurance Provider")
    _create_field(PATIENTS_MODULE_ID, "Insurance ID", "insurance_id", FieldType.TEXT, "Insurance ID")
    _create_field(PATIENTS_MODULE_ID, "Medical History", "medical_history", FieldType.TEXT, "Medical History")
    _create_field(PATIENTS_MODULE_ID, "Allergies", "allergies", FieldType.TEXT, "Allergies")
    status_id = _create_field(PATIENTS_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("Active", "Active"), ("Discharged", "Discharged"),
                                     ("Transferred", "Transferred"), ("Deceased", "Deceased")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "Active"), order=i)


def _seed_visits_module():
    global VISITS_MODULE_ID
    VISITS_MODULE_ID = _create_module("visits", "visits", "Visit", "Visits", "Patient visits")
    _create_field(VISITS_MODULE_ID, "Visit ID", "visit_id", FieldType.AUTO_NUMBER, "Visit ID", is_unique=True)
    _create_field(VISITS_MODULE_ID, "Patient ID", "patient_lookup", FieldType.LOOKUP, "Patient",
                  is_required=True, lookup_module_id=PATIENTS_MODULE_ID)
    _create_field(VISITS_MODULE_ID, "Doctor ID", "doctor_lookup", FieldType.LOOKUP, "Doctor",
                  is_required=True, lookup_module_id=USERS_MODULE_ID)
    _create_field(VISITS_MODULE_ID, "Visit Date", "visit_date", FieldType.DATETIME, "Visit Date", is_required=True)
    dept_id = _create_field(VISITS_MODULE_ID, "Department", "department", FieldType.PICKLIST, "Department", is_required=True)
    for i, (val, lbl) in enumerate([("General", "General"), ("Cardiology", "Cardiology"), ("Orthopedics", "Orthopedics"),
                                     ("Pediatrics", "Pediatrics"), ("Neurology", "Neurology"), ("Oncology", "Oncology"),
                                     ("Emergency", "Emergency"), ("Surgery", "Surgery")]):
        _add_picklist(dept_id, val, lbl, order=i)
    _create_field(VISITS_MODULE_ID, "Chief Complaint", "chief_complaint", FieldType.TEXT, "Chief Complaint", is_required=True)
    _create_field(VISITS_MODULE_ID, "Diagnosis", "diagnosis", FieldType.TEXT, "Diagnosis")
    _create_field(VISITS_MODULE_ID, "Treatment", "treatment", FieldType.TEXT, "Treatment")
    _create_field(VISITS_MODULE_ID, "Blood Pressure", "vitals_bp", FieldType.TEXT, "Blood Pressure")
    _create_field(VISITS_MODULE_ID, "Temperature", "vitals_temp", FieldType.TEXT, "Temperature")
    _create_field(VISITS_MODULE_ID, "Pulse Rate", "vitals_pulse", FieldType.TEXT, "Pulse Rate")
    _create_field(VISITS_MODULE_ID, "Weight", "vitals_weight", FieldType.TEXT, "Weight")
    status_id = _create_field(VISITS_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("Scheduled", "Scheduled"), ("In-Progress", "In-Progress"),
                                     ("Completed", "Completed"), ("Cancelled", "Cancelled")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "Scheduled"), order=i)
    _create_field(VISITS_MODULE_ID, "Notes", "notes", FieldType.TEXT, "Notes")


def _seed_inventory_module():
    global INVENTORY_MODULE_ID
    INVENTORY_MODULE_ID = _create_module("inventory", "inventory", "Inventory Item", "Inventory", "Hospital inventory")
    _create_field(INVENTORY_MODULE_ID, "Item ID", "item_id", FieldType.AUTO_NUMBER, "Item ID", is_unique=True)
    _create_field(INVENTORY_MODULE_ID, "Item Name", "item_name", FieldType.TEXT, "Item Name", is_required=True)
    cat_id = _create_field(INVENTORY_MODULE_ID, "Category", "category", FieldType.PICKLIST, "Category", is_required=True)
    for i, (val, lbl) in enumerate([("Medication", "Medication"), ("Equipment", "Equipment"),
                                     ("Consumable", "Consumable"), ("Surgical", "Surgical")]):
        _add_picklist(cat_id, val, lbl, order=i)
    _create_field(INVENTORY_MODULE_ID, "Description", "description", FieldType.TEXT, "Description")
    _create_field(INVENTORY_MODULE_ID, "Quantity", "quantity", FieldType.NUMBER, "Quantity", is_required=True)
    unit_id = _create_field(INVENTORY_MODULE_ID, "Unit", "unit", FieldType.PICKLIST, "Unit", is_required=True)
    for i, (val, lbl) in enumerate([("Box", "Box"), ("Bottle", "Bottle"), ("Piece", "Piece"),
                                     ("Strip", "Strip"), ("Vial", "Vial")]):
        _add_picklist(unit_id, val, lbl, order=i)
    _create_field(INVENTORY_MODULE_ID, "Unit Price", "unit_price", FieldType.CURRENCY, "Unit Price", is_required=True)
    _create_field(INVENTORY_MODULE_ID, "Supplier", "supplier", FieldType.TEXT, "Supplier")
    _create_field(INVENTORY_MODULE_ID, "Reorder Level", "reorder_level", FieldType.NUMBER, "Reorder Level")
    _create_field(INVENTORY_MODULE_ID, "Expiry Date", "expiry_date", FieldType.DATE, "Expiry Date")
    _create_field(INVENTORY_MODULE_ID, "Batch Number", "batch_number", FieldType.TEXT, "Batch Number")
    _create_field(INVENTORY_MODULE_ID, "Location", "location", FieldType.TEXT, "Location")
    status_id = _create_field(INVENTORY_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("In-Stock", "In-Stock"), ("Low-Stock", "Low-Stock"),
                                     ("Out-of-Stock", "Out-of-Stock"), ("Expired", "Expired")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "In-Stock"), order=i)


def _seed_prescriptions_module():
    global PRESCRIPTIONS_MODULE_ID
    PRESCRIPTIONS_MODULE_ID = _create_module("prescriptions", "prescriptions", "Prescription", "Prescriptions", "Medication prescriptions")
    _create_field(PRESCRIPTIONS_MODULE_ID, "Prescription ID", "prescription_id", FieldType.AUTO_NUMBER, "Prescription ID", is_unique=True)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Patient ID", "patient_lookup", FieldType.LOOKUP, "Patient",
                  is_required=True, lookup_module_id=PATIENTS_MODULE_ID)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Doctor ID", "doctor_lookup", FieldType.LOOKUP, "Doctor",
                  is_required=True, lookup_module_id=USERS_MODULE_ID)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Visit ID", "visit_lookup", FieldType.LOOKUP, "Visit",
                  lookup_module_id=VISITS_MODULE_ID)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Prescribed Date", "prescribed_date", FieldType.DATE, "Prescribed Date", is_required=True)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Medication Name", "medication_name", FieldType.TEXT, "Medication Name", is_required=True)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Dosage", "dosage", FieldType.TEXT, "Dosage", is_required=True)
    freq_id = _create_field(PRESCRIPTIONS_MODULE_ID, "Frequency", "frequency", FieldType.PICKLIST, "Frequency", is_required=True)
    for i, (val, lbl) in enumerate([("Once daily", "Once daily"), ("Twice daily", "Twice daily"),
                                     ("Three times daily", "Three times daily"), ("As needed", "As needed")]):
        _add_picklist(freq_id, val, lbl, order=i)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Duration", "duration", FieldType.TEXT, "Duration", is_required=True)
    _create_field(PRESCRIPTIONS_MODULE_ID, "Instructions", "instructions", FieldType.TEXT, "Instructions")
    _create_field(PRESCRIPTIONS_MODULE_ID, "Refills", "refills", FieldType.NUMBER, "Refills")
    status_id = _create_field(PRESCRIPTIONS_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("Active", "Active"), ("Completed", "Completed"),
                                     ("Cancelled", "Cancelled"), ("Expired", "Expired")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "Active"), order=i)


def _seed_laboratory_module():
    global LABORATORY_MODULE_ID
    LABORATORY_MODULE_ID = _create_module("laboratory", "laboratory", "Lab Test", "Laboratory", "Laboratory tests")
    _create_field(LABORATORY_MODULE_ID, "Test ID", "test_id", FieldType.AUTO_NUMBER, "Test ID", is_unique=True)
    _create_field(LABORATORY_MODULE_ID, "Patient ID", "patient_lookup", FieldType.LOOKUP, "Patient",
                  is_required=True, lookup_module_id=PATIENTS_MODULE_ID)
    _create_field(LABORATORY_MODULE_ID, "Doctor ID", "doctor_lookup", FieldType.LOOKUP, "Doctor",
                  is_required=True, lookup_module_id=USERS_MODULE_ID)
    _create_field(LABORATORY_MODULE_ID, "Visit ID", "visit_lookup", FieldType.LOOKUP, "Visit",
                  lookup_module_id=VISITS_MODULE_ID)
    _create_field(LABORATORY_MODULE_ID, "Test Name", "test_name", FieldType.TEXT, "Test Name", is_required=True)
    type_id = _create_field(LABORATORY_MODULE_ID, "Test Type", "test_type", FieldType.PICKLIST, "Test Type", is_required=True)
    for i, (val, lbl) in enumerate([("Blood", "Blood"), ("Urine", "Urine"), ("X-Ray", "X-Ray"),
                                     ("MRI", "MRI"), ("CT Scan", "CT Scan"), ("Biopsy", "Biopsy")]):
        _add_picklist(type_id, val, lbl, order=i)
    pri_id = _create_field(LABORATORY_MODULE_ID, "Priority", "priority", FieldType.PICKLIST, "Priority", is_required=True)
    for i, (val, lbl) in enumerate([("Routine", "Routine"), ("Urgent", "Urgent"), ("Emergency", "Emergency")]):
        _add_picklist(pri_id, val, lbl, is_default=(val == "Routine"), order=i)
    _create_field(LABORATORY_MODULE_ID, "Sample Date", "sample_date", FieldType.DATETIME, "Sample Date", is_required=True)
    _create_field(LABORATORY_MODULE_ID, "Result Date", "result_date", FieldType.DATETIME, "Result Date")
    _create_field(LABORATORY_MODULE_ID, "Result Value", "result_value", FieldType.TEXT, "Result Value")
    _create_field(LABORATORY_MODULE_ID, "Reference Range", "reference_range", FieldType.TEXT, "Reference Range")
    status_id = _create_field(LABORATORY_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("Ordered", "Ordered"), ("Sample Collected", "Sample Collected"),
                                     ("In Progress", "In Progress"), ("Completed", "Completed"),
                                     ("Cancelled", "Cancelled")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "Ordered"), order=i)
    _create_field(LABORATORY_MODULE_ID, "Notes", "notes", FieldType.TEXT, "Notes")
    _create_field(LABORATORY_MODULE_ID, "Technician ID", "technician_lookup", FieldType.LOOKUP, "Technician",
                  lookup_module_id=USERS_MODULE_ID)


def _seed_relationships():
    _create_relationship(PATIENTS_MODULE_ID, VISITS_MODULE_ID, "one_to_many")
    _create_relationship(VISITS_MODULE_ID, PRESCRIPTIONS_MODULE_ID, "one_to_many")
    _create_relationship(VISITS_MODULE_ID, LABORATORY_MODULE_ID, "one_to_many")
    _create_relationship(PATIENTS_MODULE_ID, PRESCRIPTIONS_MODULE_ID, "one_to_many")
    _create_relationship(PATIENTS_MODULE_ID, LABORATORY_MODULE_ID, "one_to_many")
    _create_relationship(USERS_MODULE_ID, VISITS_MODULE_ID, "one_to_many")


def _create_default_admin():
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
            record = crud.records.create_record(CreateRecordRequest(
                context=ctx,
                module_id=USERS_MODULE_ID,
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


def _drop_all_hogc():
    session = SessionLocal()
    try:
        for table in ["related_records", "relationship_definitions",
                      "picklist_options", "records", "layouts", "fields", "modules"]:
            session.execute(db.text(f"DELETE FROM {table} WHERE tenant_id = :tid"), {"tid": Config.HOGC_TENANT_ID})
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _lookup_module_ids():
    global USERS_MODULE_ID, PATIENTS_MODULE_ID, VISITS_MODULE_ID
    global INVENTORY_MODULE_ID, PRESCRIPTIONS_MODULE_ID, LABORATORY_MODULE_ID
    existing = crud.modules.list_modules(ListModulesRequest(
        context=_ctx(), page=1, page_size=50
    ))
    for m in existing.items:
        if m.api_name == "users":
            USERS_MODULE_ID = m.id
        elif m.api_name == "patients":
            PATIENTS_MODULE_ID = m.id
        elif m.api_name == "visits":
            VISITS_MODULE_ID = m.id
        elif m.api_name == "inventory":
            INVENTORY_MODULE_ID = m.id
        elif m.api_name == "prescriptions":
            PRESCRIPTIONS_MODULE_ID = m.id
        elif m.api_name == "laboratory":
            LABORATORY_MODULE_ID = m.id


def _seed_default_data():
    """Create sample records across all modules."""
    ctx = _ctx()

    # ── Doctors / Staff ──────────────────────────────────────────────────
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
        # Create AuthUser
        auth_user = AuthUser(username=username, email=s["email"],
                             full_name=s["full_name"], role=s["role"])
        auth_user.set_password(password)
        db.session.add(auth_user)
        db.session.commit()
        # Create CRUD record
        resp = crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=USERS_MODULE_ID, data=s
        ))
        auth_user.hogc_record_id = resp.data.id
        db.session.commit()
        doctor_ids.append(resp.data.id)

    # ── Patients ─────────────────────────────────────────────────────────
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
        resp = crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=PATIENTS_MODULE_ID, data=p
        ))
        patient_ids.append(resp.data.id)

    # ── Inventory ────────────────────────────────────────────────────────
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
        crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=INVENTORY_MODULE_ID, data=item
        ))

    # ── Visits ───────────────────────────────────────────────────────────
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
         "diagnosis": "Diabetes Type 2 – controlled", "treatment": "Continue current medication",
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
        resp = crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=VISITS_MODULE_ID, data=v
        ))
        visit_ids.append(resp.data.id)

    # ── Prescriptions ────────────────────────────────────────────────────
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
        crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=PRESCRIPTIONS_MODULE_ID, data=rx
        ))

    # ── Laboratory Tests ─────────────────────────────────────────────────
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
         "result_value": "WBC: 11,200/µL, RBC: 4.5M/µL, Hgb: 13.2 g/dL, Platelets: 250K/µL",
         "reference_range": "WBC: 4,500-11,000/µL, RBC: 4.0-5.5M/µL",
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
        crud.records.create_record(CreateRecordRequest(
            context=ctx, module_id=LABORATORY_MODULE_ID, data=lab
        ))


def _do_seed():
    _seed_users_module()
    _seed_patients_module()
    _seed_visits_module()
    _seed_inventory_module()
    _seed_prescriptions_module()
    _seed_laboratory_module()
    _seed_relationships()
    _create_default_admin()
    _seed_default_data()


def seed_modules(app):
    with app.app_context():
        from hogc.engines.crud import Base as HogcBase
        HogcBase.metadata.create_all(db.engine)

        from app.auth.models import AuthUser
        db.create_all()

        existing = crud.modules.list_modules(ListModulesRequest(
            context=_ctx(), page=1, page_size=50
        ))

        if existing.total == 0:
            _do_seed()
        else:
            _lookup_module_ids()
            has_fields = False
            for m in existing.items:
                try:
                    mod_resp = crud.modules.get_module(
                        _GetReq(context=_ctx(), module_id=m.id)
                    )
                    if mod_resp.data and mod_resp.data.fields:
                        has_fields = True
                        break
                except Exception:
                    pass
            if not has_fields:
                _drop_all_hogc()
                try:
                    _do_seed()
                except Exception as e:
                    import sys
                    print(f"ERROR: Seed failed: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()


class _GetReq:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

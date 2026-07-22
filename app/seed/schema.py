"""Seed schema — Module, field, picklist, and relationship creation helpers."""
from hogc.lib import HOGC
import uuid
from app.extensions import SessionLocal, db
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateModuleRequest, CreateFieldRequest, AddPicklistOptionRequest,
    ListModulesRequest, CreateLayoutRequest,
)
from hogc.lib.contracts.crud.types import FieldType


# Module IDs - set after creation
USERS_MODULE_ID = None
PATIENTS_MODULE_ID = None
VISITS_MODULE_ID = None
INVENTORY_MODULE_ID = None
PRESCRIPTIONS_MODULE_ID = None
LABORATORY_MODULE_ID = None

# Relationship definition IDs - set after creation
PATIENTS_VISITS_REL_ID = None
VISITS_PRESCRIPTIONS_REL_ID = None
VISITS_LABORATORY_REL_ID = None
PATIENTS_PRESCRIPTIONS_REL_ID = None
PATIENTS_LABORATORY_REL_ID = None
USERS_VISITS_REL_ID = None


def _ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_module(name, api_name, label, plural_label, description=""):
    resp = HOGC.crud.module.create(CreateModuleRequest(
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
    resp = HOGC.crud.field.create(CreateFieldRequest(
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
    return resp.data.id


def _add_picklist(field_id, value, label, color=None, is_default=False, order=0):
    HOGC.crud.picklist.add_option(AddPicklistOptionRequest(
        context=_ctx(),
        field_id=field_id,
        value=value,
        label=label,
        color=color,
        is_default=is_default,
        display_order=order,
    ))


def _create_layout(module_id, name, field_order, is_default=False):
    resp = HOGC.crud.layout.create(CreateLayoutRequest(
        context=_ctx(),
        module_id=module_id,
        name=name,
        field_order=field_order,
        is_default=is_default,
    ))
    return resp.data.id


def _create_relationship(from_module_id, to_module_id, rel_type, from_field="", to_field=""):
    from hogc.engines.crud import RelationshipDefinition
    session = SessionLocal()
    try:
        rel = RelationshipDefinition(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            from_module_id=from_module_id,
            to_module_id=to_module_id,
            relationship_type=rel_type,
            from_field_name=from_field,
            to_field_name=to_field,
            cascade_delete=False,
        )
        session.add(rel)
        session.flush()
        rel_id = rel.id
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
                                     ("Pharmacist", "Pharmacist"), ("Lab Technician", "Lab Technician"),
                                     ("Receptionist", "Receptionist")]):
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
    _create_field(PATIENTS_MODULE_ID, "Assigned Doctor", "assigned_doctor", FieldType.LOOKUP, "Assigned Doctor", lookup_module_id=USERS_MODULE_ID)
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


def _seed_layouts():
    global USERS_MODULE_ID, PATIENTS_MODULE_ID, VISITS_MODULE_ID
    global INVENTORY_MODULE_ID, PRESCRIPTIONS_MODULE_ID, LABORATORY_MODULE_ID

    _create_layout(USERS_MODULE_ID, "Standard Layout", ["full_name", "email", "phone", "role", "department", "is_active"], True)
    _create_layout(PATIENTS_MODULE_ID, "Standard Layout", ["patient_id", "first_name", "last_name", "date_of_birth", "gender", "phone", "email", "assigned_doctor", "address", "blood_group", "emergency_contact", "emergency_phone", "insurance_provider", "insurance_id", "medical_history", "allergies", "status"], True)
    _create_layout(VISITS_MODULE_ID, "Standard Layout", ["visit_id", "patient_lookup", "doctor_lookup", "visit_date", "department", "chief_complaint", "diagnosis", "treatment", "vitals_bp", "vitals_temp", "vitals_pulse", "vitals_weight", "status", "notes"], True)
    _create_layout(INVENTORY_MODULE_ID, "Standard Layout", ["item_id", "item_name", "category", "description", "quantity", "unit", "unit_price", "supplier", "reorder_level", "expiry_date", "batch_number", "location", "status"], True)
    _create_layout(PRESCRIPTIONS_MODULE_ID, "Standard Layout", ["prescription_id", "patient_lookup", "doctor_lookup", "visit_lookup", "prescribed_date", "medication_name", "dosage", "frequency", "duration", "instructions", "refills", "status"], True)
    _create_layout(LABORATORY_MODULE_ID, "Standard Layout", ["test_id", "patient_lookup", "doctor_lookup", "visit_lookup", "test_name", "test_type", "priority", "sample_date", "result_date", "result_value", "reference_range", "status", "notes", "technician_lookup"], True)


def _seed_relationships():
    global PATIENTS_VISITS_REL_ID, VISITS_PRESCRIPTIONS_REL_ID, VISITS_LABORATORY_REL_ID
    global PATIENTS_PRESCRIPTIONS_REL_ID, PATIENTS_LABORATORY_REL_ID, USERS_VISITS_REL_ID
    PATIENTS_VISITS_REL_ID = _create_relationship(PATIENTS_MODULE_ID, VISITS_MODULE_ID, "one_to_many")
    VISITS_PRESCRIPTIONS_REL_ID = _create_relationship(VISITS_MODULE_ID, PRESCRIPTIONS_MODULE_ID, "one_to_many")
    VISITS_LABORATORY_REL_ID = _create_relationship(VISITS_MODULE_ID, LABORATORY_MODULE_ID, "one_to_many")
    PATIENTS_PRESCRIPTIONS_REL_ID = _create_relationship(PATIENTS_MODULE_ID, PRESCRIPTIONS_MODULE_ID, "one_to_many")
    PATIENTS_LABORATORY_REL_ID = _create_relationship(PATIENTS_MODULE_ID, LABORATORY_MODULE_ID, "one_to_many")
    USERS_VISITS_REL_ID = _create_relationship(USERS_MODULE_ID, VISITS_MODULE_ID, "one_to_many")


def _drop_all_hogc():
    session = SessionLocal()
    try:
        for table in ["related_records", "relationship_definitions",
                      "picklist_options", "records", "layouts", "fields", "modules"]:
            session.execute(db.text(f"DELETE FROM {table} WHERE tenant_id = :tid"), {"tid": Config.HOGC_TENANT_ID})
        session.execute(db.text("DELETE FROM auth_users"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _lookup_module_ids():
    global USERS_MODULE_ID, PATIENTS_MODULE_ID, VISITS_MODULE_ID
    global INVENTORY_MODULE_ID, PRESCRIPTIONS_MODULE_ID, LABORATORY_MODULE_ID
    existing = HOGC.crud.module.list(ListModulesRequest(
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
    _lookup_relationship_ids()


def _lookup_relationship_ids():
    global PATIENTS_VISITS_REL_ID, VISITS_PRESCRIPTIONS_REL_ID, VISITS_LABORATORY_REL_ID
    global PATIENTS_PRESCRIPTIONS_REL_ID, PATIENTS_LABORATORY_REL_ID, USERS_VISITS_REL_ID
    session = SessionLocal()
    try:
        rows = session.execute(db.text("""
            SELECT id, from_module_id, to_module_id, relationship_type
            FROM relationship_definitions
            WHERE tenant_id = :tid AND org_id = :oid AND status = 'active'
        """), {"tid": Config.HOGC_TENANT_ID, "oid": Config.HOGC_ORG_ID}).fetchall()
        for row in rows:
            rid, from_mid, to_mid, rtype = row
            if from_mid == PATIENTS_MODULE_ID and to_mid == VISITS_MODULE_ID:
                PATIENTS_VISITS_REL_ID = rid
            elif from_mid == VISITS_MODULE_ID and to_mid == PRESCRIPTIONS_MODULE_ID:
                VISITS_PRESCRIPTIONS_REL_ID = rid
            elif from_mid == VISITS_MODULE_ID and to_mid == LABORATORY_MODULE_ID:
                VISITS_LABORATORY_REL_ID = rid
            elif from_mid == PATIENTS_MODULE_ID and to_mid == PRESCRIPTIONS_MODULE_ID:
                PATIENTS_PRESCRIPTIONS_REL_ID = rid
            elif from_mid == PATIENTS_MODULE_ID and to_mid == LABORATORY_MODULE_ID:
                PATIENTS_LABORATORY_REL_ID = rid
            elif from_mid == USERS_MODULE_ID and to_mid == VISITS_MODULE_ID:
                USERS_VISITS_REL_ID = rid
    finally:
        session.close()

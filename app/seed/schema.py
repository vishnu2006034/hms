"""Seed schema — Module, field, picklist, and relationship creation helpers."""
import typing
from hogc.lib import HOGC
import uuid
from app import extensions
from app.extensions import db
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateModuleRequest, CreateFieldRequest, AddPicklistOptionRequest,
    ListModulesRequest, CreateLayoutRequest,
)
from hogc.lib.contracts.crud.types import FieldType
from hogc.engines.crud.schema import RelationshipDefinition


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
PATIENTS_DOCTORS_REL_ID = None


def _ctx() -> RequestContext:
    """Build a system-level RequestContext for seeding operations.

    Returns:
        A RequestContext with tenant/org from Config and the 'Admin' role.
    """
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_module(
    name: str,
    api_name: str,
    label: str,
    plural_label: str,
    description: str = "",
) -> str:
    """Create a HOGC module and return its generated UUID.

    Args:
        name: Internal machine name of the module.
        api_name: URL-safe API identifier (e.g. 'patients').
        label: Human-readable singular label.
        plural_label: Human-readable plural label.
        description: Optional description string.

    Returns:
        The UUID string of the newly created module.
    """
    resp = HOGC.crud.module.create(CreateModuleRequest(
        context=_ctx(),
        name=name,
        api_name=api_name,
        label=label,
        plural_label=plural_label,
        description=description,
    ))
    return resp.data.id


def _create_field(
    module_id: str,
    field_name: str,
    api_name: str,
    field_type: typing.Any,
    label: str = "",
    is_required: bool = False,
    is_unique: bool = False,
    default_value: typing.Optional[str] = None,
    lookup_module_id: typing.Optional[str] = None,
) -> str:
    """Create a field on a HOGC module and return its generated UUID.

    Args:
        module_id: UUID of the parent module.
        field_name: Display name of the field.
        api_name: Snake_case API identifier for the field.
        field_type: A FieldType enum value (e.g. FieldType.TEXT).
        label: Human-readable label; falls back to field_name if empty.
        is_required: Whether the field is mandatory on record creation.
        is_unique: Whether the field must be unique across records.
        default_value: Optional default value string.
        lookup_module_id: For LOOKUP/MULTI_LOOKUP fields, the target module UUID.

    Returns:
        The UUID string of the newly created field.
    """
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


def _add_picklist(
    field_id: str,
    value: str,
    label: str,
    color: typing.Optional[str] = None,
    is_default: bool = False,
    order: int = 0,
) -> None:
    """Add a picklist option to an existing PICKLIST or MULTI_PICKLIST field.

    Args:
        field_id: UUID of the target picklist field.
        value: The stored value for this option (e.g. 'Active').
        label: The display label shown to users.
        color: Optional hex colour string for UI badging (e.g. '#28a745').
        is_default: Whether this option is pre-selected by default.
        order: Display order index among the picklist options.
    """
    HOGC.crud.picklist.add_option(AddPicklistOptionRequest(
        context=_ctx(),
        field_id=field_id,
        value=value,
        label=label,
        color=color,
        is_default=is_default,
        display_order=order,
    ))


def _create_layout(
    module_id: str,
    name: str,
    field_order: list[str],
    is_default: bool = False,
) -> str:
    """Create a layout for a module and return its generated UUID.

    Args:
        module_id: UUID of the parent module.
        name: Display name for the layout (e.g. 'Standard Layout').
        field_order: Ordered list of field api_names defining the layout columns.
        is_default: Whether this layout is the module's default view.

    Returns:
        The UUID string of the newly created layout.
    """
    resp = HOGC.crud.layout.create(CreateLayoutRequest(
        context=_ctx(),
        module_id=module_id,
        name=name,
        field_order=field_order,
        is_default=is_default,
    ))
    return resp.data.id





def _seed_users_module() -> None:
    """Create the 'users' module with all its fields and picklist options.

    Sets the module-level USERS_MODULE_ID global after creation.
    """
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


def _seed_patients_module() -> None:
    """Create the 'patients' module with all its fields and picklist options.

    Sets the module-level PATIENTS_MODULE_ID global after creation.
    """
    global PATIENTS_MODULE_ID
    PATIENTS_MODULE_ID = _create_module("patients", "patients", "Patient", "Patients", "Patient records")
    _create_field(PATIENTS_MODULE_ID, "Patient ID", "patient_id", FieldType.AUTO_NUMBER, "Patient ID", is_unique=True)
    _create_field(PATIENTS_MODULE_ID, "First Name", "first_name", FieldType.TEXT, "First Name", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Last Name", "last_name", FieldType.TEXT, "Last Name", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Date of Birth", "date_of_birth", FieldType.DATE, "Date of Birth", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Age", "age", FieldType.NUMBER, "Age")
    gender_id = _create_field(PATIENTS_MODULE_ID, "Gender", "gender", FieldType.PICKLIST, "Gender", is_required=True)
    for i, (val, lbl) in enumerate([("Male", "Male"), ("Female", "Female"), ("Other", "Other")]):
        _add_picklist(gender_id, val, lbl, order=i)
    _create_field(PATIENTS_MODULE_ID, "Phone", "phone", FieldType.PHONE, "Phone", is_required=True)
    _create_field(PATIENTS_MODULE_ID, "Email", "email", FieldType.EMAIL, "Email")
    _create_field(PATIENTS_MODULE_ID, "Assigned Doctors", "assigned_doctors", FieldType.MULTI_LOOKUP, "Assigned Doctors", lookup_module_id=USERS_MODULE_ID)
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
    alg_id = _create_field(PATIENTS_MODULE_ID, "Allergies", "allergies", FieldType.MULTI_PICKLIST, "Allergies")
    for i, (val, lbl) in enumerate([("Penicillin", "Penicillin"), ("Peanuts", "Peanuts"), ("Latex", "Latex"), 
                                     ("Dust", "Dust"), ("Pollen", "Pollen"), ("Other", "Other")]):
        _add_picklist(alg_id, val, lbl, order=i)
    status_id = _create_field(PATIENTS_MODULE_ID, "Status", "status", FieldType.PICKLIST, "Status", is_required=True)
    for i, (val, lbl) in enumerate([("Active", "Active"), ("Discharged", "Discharged"),
                                     ("Transferred", "Transferred"), ("Deceased", "Deceased")]):
        _add_picklist(status_id, val, lbl, is_default=(val == "Active"), order=i)


def _seed_visits_module() -> None:
    """Create the 'visits' module with all its fields and picklist options.

    Sets the module-level VISITS_MODULE_ID global after creation.
    """
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
    symp_id = _create_field(VISITS_MODULE_ID, "Symptoms", "symptoms", FieldType.MULTI_PICKLIST, "Symptoms")
    for i, (val, lbl) in enumerate([("Fever", "Fever"), ("Cough", "Cough"), ("Headache", "Headache"),
                                     ("Nausea", "Nausea"), ("Fatigue", "Fatigue"), ("Other", "Other")]):
        _add_picklist(symp_id, val, lbl, order=i)
    _create_field(VISITS_MODULE_ID, "Notes", "notes", FieldType.TEXT, "Notes")


def _seed_inventory_module() -> None:
    """Create the 'inventory' module with all its fields and picklist options.

    Sets the module-level INVENTORY_MODULE_ID global after creation.
    """
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


def _seed_prescriptions_module() -> None:
    """Create the 'prescriptions' module with all its fields and picklist options.

    Sets the module-level PRESCRIPTIONS_MODULE_ID global after creation.
    """
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


def _seed_laboratory_module() -> None:
    """Create the 'laboratory' module with all its fields and picklist options.

    Sets the module-level LABORATORY_MODULE_ID global after creation.
    """
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


def _seed_layouts() -> None:
    """Create the default Standard Layout for every seeded module.

    Depends on all six module ID globals being set before this is called.
    """
    global USERS_MODULE_ID, PATIENTS_MODULE_ID, VISITS_MODULE_ID
    global INVENTORY_MODULE_ID, PRESCRIPTIONS_MODULE_ID, LABORATORY_MODULE_ID

    _create_layout(USERS_MODULE_ID, "Standard Layout", ["full_name", "email", "phone", "role", "department", "is_active"], True)
    _create_layout(PATIENTS_MODULE_ID, "Standard Layout", ["patient_id", "first_name", "last_name", "age", "date_of_birth", "gender", "phone", "email", "assigned_doctors", "address", "blood_group", "emergency_contact", "emergency_phone", "insurance_provider", "insurance_id", "medical_history", "allergies", "status"], True)
    _create_layout(VISITS_MODULE_ID, "Standard Layout", ["visit_id", "patient_lookup", "doctor_lookup", "visit_date", "department", "chief_complaint", "diagnosis", "symptoms", "treatment", "vitals_bp", "vitals_temp", "vitals_pulse", "vitals_weight", "status", "notes"], True)
    _create_layout(INVENTORY_MODULE_ID, "Standard Layout", ["item_id", "item_name", "category", "description", "quantity", "unit", "unit_price", "supplier", "reorder_level", "expiry_date", "batch_number", "location", "status"], True)
    _create_layout(PRESCRIPTIONS_MODULE_ID, "Standard Layout", ["prescription_id", "patient_lookup", "doctor_lookup", "visit_lookup", "prescribed_date", "medication_name", "dosage", "frequency", "duration", "instructions", "refills", "status"], True)
    _create_layout(LABORATORY_MODULE_ID, "Standard Layout", ["test_id", "patient_lookup", "doctor_lookup", "visit_lookup", "test_name", "test_type", "priority", "sample_date", "result_date", "result_value", "reference_range", "status", "notes", "technician_lookup"], True)





def _drop_all_hogc() -> None:
    """Delete all HOGC records for the configured tenant, then truncate auth_users.

    Executes DELETE statements for every HOGC table in dependency order so
    that foreign-key constraints are satisfied.  Rolls back automatically on
    any exception and always closes the session.
    """
    session = extensions.SessionLocal()
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


def _lookup_module_ids() -> None:
    """Populate the module ID globals by querying existing HOGC modules.

    Reads all modules for the configured tenant and sets each of the six
    module-level ID globals (USERS_MODULE_ID, PATIENTS_MODULE_ID, etc.).
    Calls _lookup_relationship_ids() once all IDs are resolved.
    """
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


def _lookup_relationship_ids() -> None:
    """Populate relationship ID globals by querying relationship_definitions directly.

    Runs a raw SQL SELECT against the relationship_definitions table to find
    the UUIDs of the six predefined inter-module relationships and assigns
    each to its corresponding module-level global constant.
    """
    global PATIENTS_VISITS_REL_ID, VISITS_PRESCRIPTIONS_REL_ID, VISITS_LABORATORY_REL_ID
    global PATIENTS_PRESCRIPTIONS_REL_ID, PATIENTS_LABORATORY_REL_ID, USERS_VISITS_REL_ID
    global PATIENTS_DOCTORS_REL_ID
    session = extensions.SessionLocal()
    try:
        rows = session.execute(db.text("""
            SELECT id, from_module_id, to_module_id, relationship_type, from_field_name
            FROM relationship_definitions
            WHERE tenant_id = :tid AND org_id = :oid AND status = 'active'
        """), {"tid": Config.HOGC_TENANT_ID, "oid": Config.HOGC_ORG_ID}).fetchall()
        for row in rows:
            rid, from_mid, to_mid, rtype, from_field = row
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
            elif from_mid == PATIENTS_MODULE_ID and to_mid == USERS_MODULE_ID and rtype == "many_to_many":
                PATIENTS_DOCTORS_REL_ID = rid
    finally:
        session.close()

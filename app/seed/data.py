"""Seed data — Default admin user, staff accounts, inventory, patients, visits, prescriptions, and lab tests."""
import typing

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest, LinkRecordsRequest

from app.config import Config
from app.extensions import db
from app.modules.routes_base import _sync_related_record_on_create
from app.seed import schema


def _ctx() -> RequestContext:
    """Build a system-level RequestContext for seed data operations.

    Returns:
        A RequestContext populated with tenant/org from Config and the 'Admin' role.
    """
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_default_admin(module_id: str) -> None:
    """Ensure a default admin AuthUser and matching HOGC record exist.

    Creates both the SQLAlchemy AuthUser row and the corresponding HOGC
    record in the users module only when no admin user exists yet.
    Silently ignores failures when creating the HOGC record.

    Args:
        module_id: UUID of the 'users' HOGC module, used when creating the
                   corresponding HOGC record for the admin user.
    """
    from app.auth.models import AuthUser
    admin: typing.Optional[AuthUser] = AuthUser.query.filter_by(username="admin").first()
    if admin is None:
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
            ctx: RequestContext = _ctx()
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


def _seed_staff(users_module_id: str) -> dict[str, str]:
    """Create staff AuthUser records and matching HOGC users records.

    Args:
        users_module_id: UUID of the 'users' HOGC module.

    Returns:
        Dict mapping doctor/staff key identifier to their created HOGC record UUID.
    """
    from app.auth.models import AuthUser

    ctx: RequestContext = _ctx()
    staff_definitions: list[dict[str, str]] = [
        {
            "key": "dr_sarah_johnson",
            "full_name": "Dr. Sarah Johnson",
            "email": "sarah.johnson@hospital.com",
            "phone": "+911234567891",
            "role": "Doctor",
            "department": "Cardiology",
            "is_active": "true",
            "username": "sarah.johnson",
            "password": "password123",
        },
        {
            "key": "dr_james_patel",
            "full_name": "Dr. James Patel",
            "email": "james.patel@hospital.com",
            "phone": "+919876543210",
            "role": "Doctor",
            "department": "Neurology",
            "is_active": "true",
            "username": "james.patel",
            "password": "password123",
        },
        {
            "key": "dr_emily_chen",
            "full_name": "Dr. Emily Chen",
            "email": "emily.chen@hospital.com",
            "phone": "+919876543211",
            "role": "Doctor",
            "department": "Pediatrics",
            "is_active": "true",
            "username": "emily.chen",
            "password": "password123",
        },
        {
            "key": "dr_robert_williams",
            "full_name": "Dr. Robert Williams",
            "email": "robert.williams@hospital.com",
            "phone": "+919876543212",
            "role": "Doctor",
            "department": "Orthopedics",
            "is_active": "true",
            "username": "robert.williams",
            "password": "password123",
        },
        {
            "key": "nurse_linda_davis",
            "full_name": "Linda Davis",
            "email": "linda.davis@hospital.com",
            "phone": "+919876543213",
            "role": "Nurse",
            "department": "General",
            "is_active": "true",
            "username": "linda.davis",
            "password": "password123",
        },
        {
            "key": "pharm_mark_evans",
            "full_name": "Mark Evans",
            "email": "mark.evans@hospital.com",
            "phone": "+919876543214",
            "role": "Pharmacist",
            "department": "Pharmacy",
            "is_active": "true",
            "username": "mark.evans",
            "password": "password123",
        },
        {
            "key": "tech_priya_sharma",
            "full_name": "Priya Sharma",
            "email": "priya.sharma@hospital.com",
            "phone": "+919876543215",
            "role": "Lab Technician",
            "department": "Laboratory",
            "is_active": "true",
            "username": "priya.sharma",
            "password": "password123",
        },
        {
            "key": "recep_david_miller",
            "full_name": "David Miller",
            "email": "david.miller@hospital.com",
            "phone": "+919876543216",
            "role": "Receptionist",
            "department": "Front Desk",
            "is_active": "true",
            "username": "david.miller",
            "password": "password123",
        },
    ]

    staff_id_map: dict[str, str] = {}

    for item in staff_definitions:
        staff_key: str = item["key"]
        username: str = item["username"]
        password: str = item["password"]
        email: str = item["email"]
        full_name: str = item["full_name"]
        role: str = item["role"]
        department: str = item["department"]
        phone: str = item["phone"]
        is_active: str = item["is_active"]

        auth_user: typing.Optional[AuthUser] = AuthUser.query.filter_by(username=username).first()
        if auth_user is None:
            auth_user = AuthUser(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
            )
            auth_user.set_password(password)
            db.session.add(auth_user)
            db.session.commit()

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=users_module_id,
            data={
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "role": role,
                "department": department,
                "is_active": is_active,
            },
        ))
        auth_user.hogc_record_id = resp.data.id
        db.session.commit()
        staff_id_map[staff_key] = resp.data.id

    return staff_id_map


def _seed_inventory(inventory_module_id: str) -> None:
    """Create sample inventory items across categories.

    Args:
        inventory_module_id: UUID of the 'inventory' HOGC module.
    """
    ctx: RequestContext = _ctx()
    inventory_items: list[dict[str, str]] = [
        {
            "item_name": "Paracetamol 500mg",
            "category": "Medication",
            "description": "Fever and pain relief tablets",
            "quantity": "500",
            "unit": "Strip",
            "unit_price": "25.00",
            "supplier": "Cipla Ltd",
            "reorder_level": "100",
            "expiry_date": "2027-06-30",
            "batch_number": "PCM-2026-A1",
            "location": "Pharmacy Store A",
            "status": "In-Stock",
        },
        {
            "item_name": "Amoxicillin 250mg",
            "category": "Medication",
            "description": "Broad-spectrum antibiotic capsules",
            "quantity": "200",
            "unit": "Strip",
            "unit_price": "45.00",
            "supplier": "Sun Pharma",
            "reorder_level": "50",
            "expiry_date": "2027-03-15",
            "batch_number": "AMX-2026-B3",
            "location": "Pharmacy Store A",
            "status": "In-Stock",
        },
        {
            "item_name": "Surgical Gloves (Medium)",
            "category": "Consumable",
            "description": "Latex-free sterile surgical gloves",
            "quantity": "50",
            "unit": "Box",
            "unit_price": "350.00",
            "supplier": "MedLine Industries",
            "reorder_level": "20",
            "expiry_date": "2028-12-31",
            "batch_number": "SG-2026-M1",
            "location": "Central Store",
            "status": "In-Stock",
        },
        {
            "item_name": "Digital Thermometer",
            "category": "Equipment",
            "description": "Clinical digital thermometer with memory",
            "quantity": "15",
            "unit": "Piece",
            "unit_price": "450.00",
            "supplier": "Omron Healthcare",
            "reorder_level": "5",
            "expiry_date": "",
            "batch_number": "DT-2026-01",
            "location": "Ward Supply Room",
            "status": "In-Stock",
        },
        {
            "item_name": "Insulin Glargine 100IU/ml",
            "category": "Medication",
            "description": "Long-acting insulin for diabetes management",
            "quantity": "30",
            "unit": "Vial",
            "unit_price": "1200.00",
            "supplier": "Sanofi India",
            "reorder_level": "10",
            "expiry_date": "2027-01-20",
            "batch_number": "INS-2026-G5",
            "location": "Cold Storage",
            "status": "In-Stock",
        },
        {
            "item_name": "Sterile Gauze Swabs 10x10cm",
            "category": "Consumable",
            "description": "Individually wrapped sterile absorbent cotton gauze pads",
            "quantity": "300",
            "unit": "Box",
            "unit_price": "120.00",
            "supplier": "Johnson & Johnson MedTech",
            "reorder_level": "60",
            "expiry_date": "2029-05-15",
            "batch_number": "GZ-2026-S4",
            "location": "Central Store",
            "status": "In-Stock",
        },
        {
            "item_name": "Disposable Syringes 5ml",
            "category": "Consumable",
            "description": "Luer lock sterile single-use hypodermic syringes with needle",
            "quantity": "450",
            "unit": "Piece",
            "unit_price": "12.50",
            "supplier": "BD Healthcare",
            "reorder_level": "100",
            "expiry_date": "2029-01-10",
            "batch_number": "SYR-2026-05",
            "location": "Nursing Station Store",
            "status": "In-Stock",
        },
        {
            "item_name": "N95 Respirator Masks",
            "category": "Consumable",
            "description": "Particulate respirator face mask with adjustable nose clip",
            "quantity": "250",
            "unit": "Box",
            "unit_price": "550.00",
            "supplier": "3M India",
            "reorder_level": "50",
            "expiry_date": "2028-08-31",
            "batch_number": "MSK-2026-N95",
            "location": "Central Store",
            "status": "In-Stock",
        },
        {
            "item_name": "Scalpel Blades No. 10",
            "category": "Surgical",
            "description": "Carbon steel surgical scalpel blades, sterile foil packed",
            "quantity": "80",
            "unit": "Box",
            "unit_price": "420.00",
            "supplier": "Swann-Morton",
            "reorder_level": "25",
            "expiry_date": "2028-11-20",
            "batch_number": "SCP-2026-10",
            "location": "Operation Theatre Store",
            "status": "In-Stock",
        },
        {
            "item_name": "Fingertip Pulse Oximeter",
            "category": "Equipment",
            "description": "OLED display pulse oximeter for SpO2 and PR monitoring",
            "quantity": "20",
            "unit": "Piece",
            "unit_price": "950.00",
            "supplier": "Beurer Medical",
            "reorder_level": "8",
            "expiry_date": "",
            "batch_number": "POX-2026-F1",
            "location": "Ward Supply Room",
            "status": "In-Stock",
        },
    ]

    for item in inventory_items:
        HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=inventory_module_id,
            data=item,
        ))


def _seed_patients(patients_module_id: str, staff_ids: dict[str, str]) -> dict[str, str]:
    """Create sample patient records and link them to assigned doctors.

    Args:
        patients_module_id: UUID of the 'patients' HOGC module.
        staff_ids: Dict mapping staff keys to their HOGC record UUIDs.

    Returns:
        Dict mapping patient key identifier to their created HOGC record UUID.
    """
    ctx: RequestContext = _ctx()

    doc_sarah: str = staff_ids.get("dr_sarah_johnson", "")
    doc_james: str = staff_ids.get("dr_james_patel", "")
    doc_emily: str = staff_ids.get("dr_emily_chen", "")
    doc_robert: str = staff_ids.get("dr_robert_williams", "")

    patient_definitions: list[dict[str, typing.Any]] = [
        {
            "key": "pat_johnathan_doe",
            "first_name": "Johnathan",
            "last_name": "Doe",
            "date_of_birth": "1978-05-14",
            "age": "48",
            "gender": "Male",
            "phone": "+919876543201",
            "email": "johnathan.doe@example.com",
            "address": "104 Greenfield Avenue, Block B, New Delhi",
            "blood_group": "O+",
            "emergency_contact": "Jane Doe (Wife)",
            "emergency_phone": "+919876543202",
            "insurance_provider": "Star Health Insurance",
            "insurance_id": "SH-2024-9981",
            "medical_history": "Chronic essential hypertension diagnosed 2020. Mild right knee osteoarthritis.",
            "allergies": "Penicillin",
            "status": "Active",
            "doctors": [doc_sarah, doc_robert],
        },
        {
            "key": "pat_anita_desai",
            "first_name": "Anita",
            "last_name": "Desai",
            "date_of_birth": "1989-11-23",
            "age": "36",
            "gender": "Female",
            "phone": "+919876543203",
            "email": "anita.desai@example.com",
            "address": "12 Lakeview Residency, Sector 14, Gurgaon",
            "blood_group": "A+",
            "emergency_contact": "Vikram Desai (Husband)",
            "emergency_phone": "+919876543204",
            "insurance_provider": "Max Bupa Health",
            "insurance_id": "MB-883102",
            "medical_history": "Recurrent migraine headaches with visual aura. Seasonal allergic rhinitis.",
            "allergies": "Dust,Pollen",
            "status": "Active",
            "doctors": [doc_james],
        },
        {
            "key": "pat_marcus_vance",
            "first_name": "Marcus",
            "last_name": "Vance",
            "date_of_birth": "2018-03-15",
            "age": "8",
            "gender": "Male",
            "phone": "+919876543205",
            "email": "marcus.family@example.com",
            "address": "45 Park Street, Flat 3A, Bangalore",
            "blood_group": "B+",
            "emergency_contact": "Clara Vance (Mother)",
            "emergency_phone": "+919876543206",
            "insurance_provider": "HDFC ERGO Health",
            "insurance_id": "HE-774910",
            "medical_history": "Childhood bronchial asthma diagnosed at age 4. Mild eczema.",
            "allergies": "Peanuts",
            "status": "Active",
            "doctors": [doc_emily],
        },
        {
            "key": "pat_eleanor_wright",
            "first_name": "Eleanor",
            "last_name": "Wright",
            "date_of_birth": "1962-08-09",
            "age": "64",
            "gender": "Female",
            "phone": "+919876543207",
            "email": "eleanor.wright@example.com",
            "address": "78 Rosewood Lane, Pune",
            "blood_group": "AB-",
            "emergency_contact": "Thomas Wright (Son)",
            "emergency_phone": "+919876543208",
            "insurance_provider": "ICICI Lombard Health",
            "insurance_id": "IL-551920",
            "medical_history": "Type 2 Diabetes Mellitus (managed). Total knee replacement left knee (2022).",
            "allergies": "Latex",
            "status": "Active",
            "doctors": [doc_robert, doc_sarah],
        },
        {
            "key": "pat_rajesh_kumar",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "date_of_birth": "1995-02-17",
            "age": "31",
            "gender": "Male",
            "phone": "+919876543209",
            "email": "rajesh.k@example.com",
            "address": "202 Cyber Heights, Hitec City, Hyderabad",
            "blood_group": "O-",
            "emergency_contact": "Sunita Kumar (Mother)",
            "emergency_phone": "+919876543210",
            "insurance_provider": "Care Health Insurance",
            "insurance_id": "CHI-110293",
            "medical_history": "No chronic systemic illness. Uncomplicated appendectomy in 2018.",
            "allergies": "Other",
            "status": "Active",
            "doctors": [doc_sarah],
        },
        {
            "key": "pat_maria_rodriguez",
            "first_name": "Maria",
            "last_name": "Rodriguez",
            "date_of_birth": "1982-07-30",
            "age": "44",
            "gender": "Female",
            "phone": "+919876543211",
            "email": "maria.rod@example.com",
            "address": "15 Sunrise Boulevard, Chennai",
            "blood_group": "B-",
            "emergency_contact": "Carlos Rodriguez (Brother)",
            "emergency_phone": "+919876543212",
            "insurance_provider": "Bajaj Allianz General",
            "insurance_id": "BA-339182",
            "medical_history": "Hypothyroidism on Eltroxin therapy. Cervical spondylosis with radiculopathy.",
            "allergies": "Dust",
            "status": "Active",
            "doctors": [doc_james, doc_robert],
        },
        {
            "key": "pat_aravind_swami",
            "first_name": "Aravind",
            "last_name": "Swaminathan",
            "date_of_birth": "1955-12-04",
            "age": "70",
            "gender": "Male",
            "phone": "+919876543213",
            "email": "aravind.swamy@example.com",
            "address": "88 Palm Grove, Kochi",
            "blood_group": "A-",
            "emergency_contact": "Lakshmi Swaminathan (Daughter)",
            "emergency_phone": "+919876543214",
            "insurance_provider": "New India Assurance",
            "insurance_id": "NIA-991024",
            "medical_history": "Coronary Artery Bypass Graft (CABG) in 2021. Mixed dyslipidemia. Mild peripheral edema.",
            "allergies": "Penicillin,Latex",
            "status": "Active",
            "doctors": [doc_sarah],
        },
        {
            "key": "pat_sophie_taylor",
            "first_name": "Sophie",
            "last_name": "Taylor",
            "date_of_birth": "2012-09-18",
            "age": "13",
            "gender": "Female",
            "phone": "+919876543215",
            "email": "sophie.family@example.com",
            "address": "56 Oakridge Drive, Mumbai",
            "blood_group": "O+",
            "emergency_contact": "Karen Taylor (Mother)",
            "emergency_phone": "+919876543216",
            "insurance_provider": "Star Health Insurance",
            "insurance_id": "SH-2025-4412",
            "medical_history": "Recurrent episodes of acute streptococcal tonsillitis. Completed antibiotic course.",
            "allergies": "Pollen",
            "status": "Discharged",
            "doctors": [doc_emily],
        },
    ]

    patient_id_map: dict[str, str] = {}

    for p in patient_definitions:
        pat_key: str = p["key"]
        doc_list: list[str] = [d for d in p.get("doctors", []) if d]
        assigned_str: str = ",".join(doc_list)

        raw_payload: dict[str, str] = {
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "date_of_birth": p["date_of_birth"],
            "age": p["age"],
            "gender": p["gender"],
            "phone": p["phone"],
            "email": p["email"],
            "address": p["address"],
            "blood_group": p["blood_group"],
            "emergency_contact": p["emergency_contact"],
            "emergency_phone": p["emergency_phone"],
            "insurance_provider": p["insurance_provider"],
            "insurance_id": p["insurance_id"],
            "medical_history": p["medical_history"],
            "allergies": p["allergies"],
            "status": p["status"],
            "assigned_doctors": assigned_str,
        }

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=patients_module_id,
            data=raw_payload,
        ))
        patient_id: str = resp.data.id
        patient_id_map[pat_key] = patient_id

        # Link many-to-many doctors
        if schema.PATIENTS_DOCTORS_REL_ID:
            for doc_id in doc_list:
                try:
                    HOGC.crud.related_records.link(LinkRecordsRequest(
                        context=ctx,
                        relationship_id=schema.PATIENTS_DOCTORS_REL_ID,
                        from_record_id=patient_id,
                        to_record_id=doc_id,
                        attributes={},
                    ))
                except Exception:
                    pass

    return patient_id_map


def _seed_visits(
    visits_module_id: str,
    patient_ids: dict[str, str],
    staff_ids: dict[str, str],
) -> dict[str, str]:
    """Create sample patient visit records and link related records.

    Args:
        visits_module_id: UUID of the 'visits' HOGC module.
        patient_ids: Dict mapping patient keys to their HOGC record UUIDs.
        staff_ids: Dict mapping staff keys to their HOGC record UUIDs.

    Returns:
        Dict mapping visit key identifier to their created HOGC record UUID.
    """
    ctx: RequestContext = _ctx()

    doc_sarah: str = staff_ids.get("dr_sarah_johnson", "")
    doc_james: str = staff_ids.get("dr_james_patel", "")
    doc_emily: str = staff_ids.get("dr_emily_chen", "")
    doc_robert: str = staff_ids.get("dr_robert_williams", "")

    visit_definitions: list[dict[str, str]] = [
        {
            "key": "visit_johnathan_cardio",
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_sarah,
            "visit_date": "2026-08-10T09:30:00",
            "department": "Cardiology",
            "chief_complaint": "Exertional chest tightness and shortness of breath upon climbing stairs",
            "diagnosis": "Stable Angina Pectoris, Grade II Essential Hypertension",
            "treatment": "Initiated Beta-blocker (Metoprolol) and ACE inhibitor (Ramipril). Ordered lipid panel and ECG.",
            "vitals_bp": "148/92 mmHg",
            "vitals_temp": "98.4 F",
            "vitals_pulse": "82 bpm",
            "vitals_weight": "84 kg",
            "status": "Completed",
            "symptoms": "Fatigue,Other",
            "notes": "Patient advised on low-sodium diet and stress reduction. Follow-up scheduled in 4 weeks.",
        },
        {
            "key": "visit_johnathan_ortho",
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_robert,
            "visit_date": "2026-08-12T14:00:00",
            "department": "Orthopedics",
            "chief_complaint": "Persistent right knee joint pain and morning stiffness",
            "diagnosis": "Right Knee Osteoarthritis (Grade 2 Medial Compartment)",
            "treatment": "Prescribed oral NSAID short-course, topical analgesic gel, and quadriceps strengthening physiotherapy.",
            "vitals_bp": "138/86 mmHg",
            "vitals_temp": "98.6 F",
            "vitals_pulse": "76 bpm",
            "vitals_weight": "84 kg",
            "status": "Completed",
            "symptoms": "Other",
            "notes": "X-ray confirmed mild joint space narrowing. Avoid high-impact jogging.",
        },
        {
            "key": "visit_anita_neuro",
            "patient_key": "pat_anita_desai",
            "doctor_id": doc_james,
            "visit_date": "2026-08-11T11:00:00",
            "department": "Neurology",
            "chief_complaint": "Severe pulsating unilateral left-sided headache with photophobia and nausea for 2 days",
            "diagnosis": "Acute Migraine Attack with Visual Aura",
            "treatment": "Administered oral Sumatriptan 50mg, IV hydration fluids, and prescribed abortive triptan regimen.",
            "vitals_bp": "118/74 mmHg",
            "vitals_temp": "98.6 F",
            "vitals_pulse": "72 bpm",
            "vitals_weight": "58 kg",
            "status": "Completed",
            "symptoms": "Headache,Nausea",
            "notes": "Neurological examination cranial nerves intact. Advised keeping a headache trigger diary.",
        },
        {
            "key": "visit_marcus_peds",
            "patient_key": "pat_marcus_vance",
            "doctor_id": doc_emily,
            "visit_date": "2026-08-13T10:15:00",
            "department": "Pediatrics",
            "chief_complaint": "Nocturnal dry cough and mild expiratory wheeze after playground activity",
            "diagnosis": "Mild Persistent Bronchial Asthma Exacerbation",
            "treatment": "Prescribed Fluticasone propionate inhaler via spacer device twice daily, with Salbutamol as rescue.",
            "vitals_bp": "100/65 mmHg",
            "vitals_temp": "98.2 F",
            "vitals_pulse": "90 bpm",
            "vitals_weight": "26 kg",
            "status": "Completed",
            "symptoms": "Cough,Fatigue",
            "notes": "Correct metered dose inhaler technique demonstrated to patient and parent.",
        },
        {
            "key": "visit_eleanor_ortho",
            "patient_key": "pat_eleanor_wright",
            "doctor_id": doc_robert,
            "visit_date": "2026-08-14T15:30:00",
            "department": "Orthopedics",
            "chief_complaint": "Routine post-surgical review and mild stiffness in left knee after prolonged sitting",
            "diagnosis": "Post-Total Knee Arthroplasty (TKA) Rehabilitation, satisfactory recovery",
            "treatment": "Advised continuation of daily range of motion exercises and low-resistance stationary bicycling.",
            "vitals_bp": "132/80 mmHg",
            "vitals_temp": "98.5 F",
            "vitals_pulse": "74 bpm",
            "vitals_weight": "69 kg",
            "status": "Completed",
            "symptoms": "Other",
            "notes": "Knee active flexion 115 degrees, no effusion or erythema around surgical scar.",
        },
        {
            "key": "visit_eleanor_cardio",
            "patient_key": "pat_eleanor_wright",
            "doctor_id": doc_sarah,
            "visit_date": "2026-08-16T10:00:00",
            "department": "Cardiology",
            "chief_complaint": "Annual diabetic cardiovascular risk assessment and lipid evaluation",
            "diagnosis": "Type 2 Diabetes Mellitus with Mixed Dyslipidemia",
            "treatment": "Adjusted Statin therapy to Atorvastatin 20mg at bedtime, maintained Glycemic diet regimen.",
            "vitals_bp": "128/78 mmHg",
            "vitals_temp": "98.6 F",
            "vitals_pulse": "70 bpm",
            "vitals_weight": "68.5 kg",
            "status": "Completed",
            "symptoms": "Fatigue",
            "notes": "HbA1c and fasting blood sugar ordered. Cardiovascular risk factors are well controlled.",
        },
        {
            "key": "visit_rajesh_cardio",
            "patient_key": "pat_rajesh_kumar",
            "doctor_id": doc_sarah,
            "visit_date": "2026-08-15T16:00:00",
            "department": "Cardiology",
            "chief_complaint": "Palpitations and rapid pulse following intense gym workout and energy drink consumption",
            "diagnosis": "Sinus Tachycardia secondary to dehydration and caffeine overconsumption",
            "treatment": "IV saline rehydration, rest in observation ward for 2 hours, 12-lead ECG, troponin test ordered.",
            "vitals_bp": "122/80 mmHg",
            "vitals_temp": "98.7 F",
            "vitals_pulse": "96 bpm",
            "vitals_weight": "75 kg",
            "status": "Completed",
            "symptoms": "Fatigue,Other",
            "notes": "Post-observation pulse settled to 74 bpm. Patient counselled against high-caffeine supplements.",
        },
        {
            "key": "visit_maria_neuro",
            "patient_key": "pat_maria_rodriguez",
            "doctor_id": doc_james,
            "visit_date": "2026-08-17T09:00:00",
            "department": "Neurology",
            "chief_complaint": "Neck stiffness radiating into right shoulder and occasional paresthesias in right index finger",
            "diagnosis": "Cervical Radiculopathy (suspected C6-C7 nerve root compression)",
            "treatment": "Prescribed short-course oral muscle relaxant, soft cervical collar for sleep, ordered Cervical Spine MRI.",
            "vitals_bp": "124/82 mmHg",
            "vitals_temp": "98.4 F",
            "vitals_pulse": "68 bpm",
            "vitals_weight": "63 kg",
            "status": "In-Progress",
            "symptoms": "Headache,Other",
            "notes": "Spurling's test positive on right side. MRI scheduled to assess disc herniation.",
        },
        {
            "key": "visit_aravind_cardio",
            "patient_key": "pat_aravind_swami",
            "doctor_id": doc_sarah,
            "visit_date": "2026-08-14T09:00:00",
            "department": "Cardiology",
            "chief_complaint": "Post-CABG routine cardiology review and mild bilateral pedal edema in evenings",
            "diagnosis": "Post-CABG Status (Year 5), Mild Dependent Peripheral Edema",
            "treatment": "Added Torsemide 10mg morning dose, prescribed graded compression stockings, strict fluid balance log.",
            "vitals_bp": "134/84 mmHg",
            "vitals_temp": "98.6 F",
            "vitals_pulse": "66 bpm",
            "vitals_weight": "78 kg",
            "status": "Completed",
            "symptoms": "Fatigue,Other",
            "notes": "Echocardiogram demonstrates preserved ejection fraction (LVEF 55%) and stable graft hemodynamics.",
        },
        {
            "key": "visit_sophie_peds",
            "patient_key": "pat_sophie_taylor",
            "doctor_id": doc_emily,
            "visit_date": "2026-08-08T11:30:00",
            "department": "Pediatrics",
            "chief_complaint": "Sore throat, difficulty swallowing solid food, and fever reaching 101.2 F for 2 days",
            "diagnosis": "Acute Streptococcal Pharyngotonsillitis",
            "treatment": "Completed oral Amoxicillin 250mg 7-day course, Paracetamol syrup for antipyresis, warm saline gargles.",
            "vitals_bp": "105/68 mmHg",
            "vitals_temp": "101.2 F",
            "vitals_pulse": "94 bpm",
            "vitals_weight": "42 kg",
            "status": "Completed",
            "symptoms": "Fever,Fatigue",
            "notes": "Follow-up examination reveals fully resolved tonsillar exudates and normal temperature. Discharged.",
        },
        {
            "key": "visit_johnathan_followup",
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_sarah,
            "visit_date": "2026-08-25T10:00:00",
            "department": "Cardiology",
            "chief_complaint": "Scheduled 4-week follow-up for hypertensive response and angina symptom reassessment",
            "diagnosis": "",
            "treatment": "",
            "vitals_bp": "",
            "vitals_temp": "",
            "vitals_pulse": "",
            "vitals_weight": "",
            "status": "Scheduled",
            "symptoms": "",
            "notes": "Upcoming scheduled follow-up appointment.",
        },
        {
            "key": "visit_anita_followup",
            "patient_key": "pat_anita_desai",
            "doctor_id": doc_james,
            "visit_date": "2026-08-28T14:30:00",
            "department": "Neurology",
            "chief_complaint": "Scheduled follow-up for headache diary review and prophylactic therapy consideration",
            "diagnosis": "",
            "treatment": "",
            "vitals_bp": "",
            "vitals_temp": "",
            "vitals_pulse": "",
            "vitals_weight": "",
            "status": "Scheduled",
            "symptoms": "",
            "notes": "Upcoming scheduled appointment.",
        },
    ]

    visit_id_map: dict[str, str] = {}

    for v in visit_definitions:
        visit_key: str = v["key"]
        patient_key: str = v["patient_key"]
        patient_id: str = patient_ids.get(patient_key, "")
        doctor_id: str = v["doctor_id"]

        data: dict[str, str] = {
            "patient_lookup": patient_id,
            "doctor_lookup": doctor_id,
            "visit_date": v["visit_date"],
            "department": v["department"],
            "chief_complaint": v["chief_complaint"],
            "diagnosis": v["diagnosis"],
            "treatment": v["treatment"],
            "vitals_bp": v["vitals_bp"],
            "vitals_temp": v["vitals_temp"],
            "vitals_pulse": v["vitals_pulse"],
            "vitals_weight": v["vitals_weight"],
            "status": v["status"],
            "symptoms": v["symptoms"],
            "notes": v["notes"],
        }

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=visits_module_id,
            data=data,
        ))
        visit_id: str = resp.data.id
        visit_id_map[visit_key] = visit_id

        # Sync related records (PATIENTS_VISITS_REL_ID and USERS_VISITS_REL_ID)
        _sync_related_record_on_create(ctx, visits_module_id, visit_id, data)

    return visit_id_map


def _seed_prescriptions(
    prescriptions_module_id: str,
    patient_ids: dict[str, str],
    staff_ids: dict[str, str],
    visit_ids: dict[str, str],
) -> None:
    """Create sample prescription records and link them to patients, doctors, and visits.

    Args:
        prescriptions_module_id: UUID of the 'prescriptions' HOGC module.
        patient_ids: Dict mapping patient keys to their HOGC record UUIDs.
        staff_ids: Dict mapping staff keys to their HOGC record UUIDs.
        visit_ids: Dict mapping visit keys to their HOGC record UUIDs.
    """
    ctx: RequestContext = _ctx()

    doc_sarah: str = staff_ids.get("dr_sarah_johnson", "")
    doc_james: str = staff_ids.get("dr_james_patel", "")
    doc_emily: str = staff_ids.get("dr_emily_chen", "")
    doc_robert: str = staff_ids.get("dr_robert_williams", "")

    prescription_definitions: list[dict[str, str]] = [
        {
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_sarah,
            "visit_key": "visit_johnathan_cardio",
            "prescribed_date": "2026-08-10",
            "medication_name": "Metoprolol Succinate ER 50mg",
            "dosage": "1 tablet",
            "frequency": "Once daily",
            "duration": "30 days",
            "instructions": "Take orally every morning with or immediately after a meal.",
            "refills": "3",
            "status": "Active",
        },
        {
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_sarah,
            "visit_key": "visit_johnathan_cardio",
            "prescribed_date": "2026-08-10",
            "medication_name": "Ramipril 5mg",
            "dosage": "1 capsule",
            "frequency": "Once daily",
            "duration": "30 days",
            "instructions": "Take orally at bedtime. Monitor for dry cough or dizziness.",
            "refills": "3",
            "status": "Active",
        },
        {
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_robert,
            "visit_key": "visit_johnathan_ortho",
            "prescribed_date": "2026-08-12",
            "medication_name": "Aceclofenac + Paracetamol (100mg/325mg)",
            "dosage": "1 tablet",
            "frequency": "Twice daily",
            "duration": "7 days",
            "instructions": "Take after meals. Discontinue when acute pain subsides.",
            "refills": "0",
            "status": "Completed",
        },
        {
            "patient_key": "pat_anita_desai",
            "doctor_id": doc_james,
            "visit_key": "visit_anita_neuro",
            "prescribed_date": "2026-08-11",
            "medication_name": "Sumatriptan 50mg",
            "dosage": "1 tablet",
            "frequency": "As needed",
            "duration": "15 days",
            "instructions": "Take at earliest onset of migraine attack; maximum 2 tablets in 24 hours.",
            "refills": "2",
            "status": "Active",
        },
        {
            "patient_key": "pat_marcus_vance",
            "doctor_id": doc_emily,
            "visit_key": "visit_marcus_peds",
            "prescribed_date": "2026-08-13",
            "medication_name": "Fluticasone Propionate Inhaler 50mcg",
            "dosage": "2 puffs",
            "frequency": "Twice daily",
            "duration": "60 days",
            "instructions": "Inhale via spacer chamber morning and night. Rinse mouth with water after each use.",
            "refills": "2",
            "status": "Active",
        },
        {
            "patient_key": "pat_eleanor_wright",
            "doctor_id": doc_sarah,
            "visit_key": "visit_eleanor_cardio",
            "prescribed_date": "2026-08-16",
            "medication_name": "Atorvastatin 20mg",
            "dosage": "1 tablet",
            "frequency": "Once daily",
            "duration": "90 days",
            "instructions": "Take once daily in the evening.",
            "refills": "3",
            "status": "Active",
        },
        {
            "patient_key": "pat_aravind_swami",
            "doctor_id": doc_sarah,
            "visit_key": "visit_aravind_cardio",
            "prescribed_date": "2026-08-14",
            "medication_name": "Torsemide 10mg",
            "dosage": "1 tablet",
            "frequency": "Once daily",
            "duration": "30 days",
            "instructions": "Take in the morning with a full glass of water.",
            "refills": "2",
            "status": "Active",
        },
        {
            "patient_key": "pat_sophie_taylor",
            "doctor_id": doc_emily,
            "visit_key": "visit_sophie_peds",
            "prescribed_date": "2026-08-08",
            "medication_name": "Amoxicillin 250mg",
            "dosage": "1 capsule",
            "frequency": "Three times daily",
            "duration": "7 days",
            "instructions": "Complete the full 7-day course even if symptoms improve.",
            "refills": "0",
            "status": "Completed",
        },
    ]

    for rx in prescription_definitions:
        patient_key: str = rx["patient_key"]
        visit_key: str = rx["visit_key"]
        patient_id: str = patient_ids.get(patient_key, "")
        doctor_id: str = rx["doctor_id"]
        visit_id: str = visit_ids.get(visit_key, "")

        data: dict[str, str] = {
            "patient_lookup": patient_id,
            "doctor_lookup": doctor_id,
            "visit_lookup": visit_id,
            "prescribed_date": rx["prescribed_date"],
            "medication_name": rx["medication_name"],
            "dosage": rx["dosage"],
            "frequency": rx["frequency"],
            "duration": rx["duration"],
            "instructions": rx["instructions"],
            "refills": rx["refills"],
            "status": rx["status"],
        }

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=prescriptions_module_id,
            data=data,
        ))
        rx_record_id: str = resp.data.id

        # Sync related records (PATIENTS_PRESCRIPTIONS_REL_ID and VISITS_PRESCRIPTIONS_REL_ID)
        _sync_related_record_on_create(ctx, prescriptions_module_id, rx_record_id, data)


def _seed_laboratory(
    laboratory_module_id: str,
    patient_ids: dict[str, str],
    staff_ids: dict[str, str],
    visit_ids: dict[str, str],
) -> None:
    """Create sample laboratory test records and link them to patients, doctors, and visits.

    Args:
        laboratory_module_id: UUID of the 'laboratory' HOGC module.
        patient_ids: Dict mapping patient keys to their HOGC record UUIDs.
        staff_ids: Dict mapping staff keys to their HOGC record UUIDs.
        visit_ids: Dict mapping visit keys to their HOGC record UUIDs.
    """
    ctx: RequestContext = _ctx()

    doc_sarah: str = staff_ids.get("dr_sarah_johnson", "")
    doc_james: str = staff_ids.get("dr_james_patel", "")
    doc_robert: str = staff_ids.get("dr_robert_williams", "")
    tech_priya: str = staff_ids.get("tech_priya_sharma", "")

    lab_definitions: list[dict[str, str]] = [
        {
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_sarah,
            "visit_key": "visit_johnathan_cardio",
            "test_name": "Lipid Profile Panel (Complete)",
            "test_type": "Blood",
            "priority": "Routine",
            "sample_date": "2026-08-10T10:15:00",
            "result_date": "2026-08-10T16:00:00",
            "result_value": "Total Cholesterol: 220 mg/dL, LDL: 140 mg/dL, HDL: 42 mg/dL, Triglycerides: 190 mg/dL",
            "reference_range": "Cholesterol < 200, LDL < 100, HDL > 40, TG < 150 mg/dL",
            "status": "Completed",
            "notes": "Borderline hypercholesterolemia and hypertriglyceridemia noted.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_johnathan_doe",
            "doctor_id": doc_robert,
            "visit_key": "visit_johnathan_ortho",
            "test_name": "Right Knee X-Ray AP and Lateral Views",
            "test_type": "X-Ray",
            "priority": "Routine",
            "sample_date": "2026-08-12T14:45:00",
            "result_date": "2026-08-12T17:30:00",
            "result_value": "Medial joint space narrowing, subchondral sclerosis, mild tibial osteophytes",
            "reference_range": "Normal anatomic alignment and joint space width",
            "status": "Completed",
            "notes": "Radiological findings consistent with Grade 2 medial compartment osteoarthritis.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_anita_desai",
            "doctor_id": doc_james,
            "visit_key": "visit_anita_neuro",
            "test_name": "Brain MRI with Magnetic Resonance Angiography",
            "test_type": "MRI",
            "priority": "Routine",
            "sample_date": "2026-08-11T13:00:00",
            "result_date": "2026-08-11T18:00:00",
            "result_value": "Unremarkable cerebral parenchyma. Normal ventricular system. No vascular malformation or aneurysm.",
            "reference_range": "Normal brain parenchyma and intracranial vasculature",
            "status": "Completed",
            "notes": "Normal neuroimaging rules out structural etiology for migraine attacks.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_eleanor_wright",
            "doctor_id": doc_sarah,
            "visit_key": "visit_eleanor_cardio",
            "test_name": "Glycated Hemoglobin (HbA1c) & Fasting Plasma Glucose",
            "test_type": "Blood",
            "priority": "Routine",
            "sample_date": "2026-08-16T10:30:00",
            "result_date": "2026-08-16T15:00:00",
            "result_value": "HbA1c: 6.8%, Fasting Blood Sugar: 126 mg/dL",
            "reference_range": "HbA1c < 5.7% (Normal), 5.7-6.4% (Prediabetes), >= 6.5% (Diabetes)",
            "status": "Completed",
            "notes": "Glycemic status is under acceptable therapeutic control.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_rajesh_kumar",
            "doctor_id": doc_sarah,
            "visit_key": "visit_rajesh_cardio",
            "test_name": "High-Sensitivity Cardiac Troponin I & Serum Electrolytes",
            "test_type": "Blood",
            "priority": "Urgent",
            "sample_date": "2026-08-15T16:30:00",
            "result_date": "2026-08-15T18:00:00",
            "result_value": "Troponin I: < 0.01 ng/mL (Negative), Potassium: 4.1 mEq/L, Sodium: 139 mEq/L",
            "reference_range": "Troponin I < 0.04 ng/mL, Potassium: 3.5 - 5.0 mEq/L, Sodium: 135 - 145 mEq/L",
            "status": "Completed",
            "notes": "Acute myocardial necrosis ruled out. Serum electrolytes within normal limits.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_aravind_swami",
            "doctor_id": doc_sarah,
            "visit_key": "visit_aravind_cardio",
            "test_name": "Transthoracic 2D Echocardiogram with Color Doppler",
            "test_type": "X-Ray",
            "priority": "Routine",
            "sample_date": "2026-08-14T10:30:00",
            "result_date": "2026-08-14T12:30:00",
            "result_value": "LVEF 55%, mild concentric left ventricular hypertrophy, normal valve motion, no pericardial effusion",
            "reference_range": "Left Ventricular Ejection Fraction 50 - 70%",
            "status": "Completed",
            "notes": "Stable post-surgical cardiac profile with normal ejection fraction.",
            "technician_id": tech_priya,
        },
        {
            "patient_key": "pat_maria_rodriguez",
            "doctor_id": doc_james,
            "visit_key": "visit_maria_neuro",
            "test_name": "Cervical Spine MRI (Non-Contrast)",
            "test_type": "MRI",
            "priority": "Routine",
            "sample_date": "2026-08-20T09:00:00",
            "result_date": "",
            "result_value": "",
            "reference_range": "",
            "status": "Ordered",
            "notes": "Scheduled imaging to evaluate suspected C6-C7 nerve root compression.",
            "technician_id": "",
        },
    ]

    for lab in lab_definitions:
        patient_key: str = lab["patient_key"]
        visit_key: str = lab["visit_key"]
        patient_id: str = patient_ids.get(patient_key, "")
        doctor_id: str = lab["doctor_id"]
        visit_id: str = visit_ids.get(visit_key, "")
        technician_id: str = lab.get("technician_id", "")

        data: dict[str, str] = {
            "patient_lookup": patient_id,
            "doctor_lookup": doctor_id,
            "visit_lookup": visit_id,
            "test_name": lab["test_name"],
            "test_type": lab["test_type"],
            "priority": lab["priority"],
            "sample_date": lab["sample_date"],
            "result_date": lab["result_date"],
            "result_value": lab["result_value"],
            "reference_range": lab["reference_range"],
            "status": lab["status"],
            "notes": lab["notes"],
            "technician_lookup": technician_id,
        }

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=ctx,
            module_id=laboratory_module_id,
            data=data,
        ))
        lab_record_id: str = resp.data.id

        # Sync related records (PATIENTS_LABORATORY_REL_ID and VISITS_LABORATORY_REL_ID)
        _sync_related_record_on_create(ctx, laboratory_module_id, lab_record_id, data)


def _seed_default_data(module_ids: dict[str, str]) -> None:
    """Create comprehensive sample records across all modules for demonstration purposes.

    Seeds staff members, inventory items, patient profiles, clinical visits,
    prescriptions, and laboratory diagnostics, linking records through relationships.

    Args:
        module_ids: Dict mapping module API names to their HOGC UUIDs, e.g.
                    {'users': '...', 'patients': '...', 'visits': '...', ...}.
    """
    users_id: str = module_ids["users"]
    patients_id: str = module_ids["patients"]
    visits_id: str = module_ids["visits"]
    inventory_id: str = module_ids["inventory"]
    prescriptions_id: str = module_ids["prescriptions"]
    laboratory_id: str = module_ids["laboratory"]

    schema._lookup_relationship_ids()

    # 1. Staff and Doctors
    staff_ids: dict[str, str] = _seed_staff(users_id)

    # 2. Inventory Items
    _seed_inventory(inventory_id)

    # 3. Patient Profiles and Doctor Assignments
    patient_ids: dict[str, str] = _seed_patients(patients_id, staff_ids)

    # 4. Clinical Visits
    visit_ids: dict[str, str] = _seed_visits(visits_id, patient_ids, staff_ids)

    # 5. Prescriptions
    _seed_prescriptions(prescriptions_id, patient_ids, staff_ids, visit_ids)

    # 6. Laboratory Diagnostics
    _seed_laboratory(laboratory_id, patient_ids, staff_ids, visit_ids)
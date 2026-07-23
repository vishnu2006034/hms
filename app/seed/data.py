"""Seed data — Default admin user and sample records."""
from hogc.lib import HOGC
from app.extensions import db
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest, LinkRecordsRequest
from app.config import Config
from app.seed import schema


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

   
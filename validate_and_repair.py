import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.seed import schema
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListRecordsRequest, QueryRecordsRequest, UpdateRecordRequest
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from app.config import Config
from hogc.lib.base import RequestContext
from app import create_app

app = create_app()

def run_validation_and_repair():
    print("Starting validation and repair...")
    ctx = RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )
    
    # 1. Get all patients
    patients_resp = HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=1000
    ))
    
    if not patients_resp or not patients_resp.items:
        print("No patients found.")
        return
        
    patients = patients_resp.items
    print(f"Found {len(patients)} patients.")
    
    repaired_visits = 0
    repaired_prescriptions = 0
    repaired_labs = 0
    
    for patient in patients:
        patient_id = patient.id
        assigned_doctor = patient.data.get("assigned_doctor")
        
        if not assigned_doctor:
            continue
            
        # Check visits
        query = RecordQuery(
            module_id=schema.VISITS_MODULE_ID,
            filters=[QueryFilter(field="patient_lookup", operator="eq", value=patient_id)],
            page=1, page_size=100
        )
        visits_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        
        for visit in visits_resp.items:
            visit_doctor = visit.data.get("doctor_lookup")
            if visit_doctor != assigned_doctor:
                print(f"[REPAIR] Visit {visit.id}: Changing doctor from {visit_doctor} to {assigned_doctor}")
                new_data = visit.data.copy()
                new_data["doctor_lookup"] = assigned_doctor
                HOGC.crud.record.update(UpdateRecordRequest(
                    context=ctx, module_id=schema.VISITS_MODULE_ID, record_id=visit.id, data=new_data
                ))
                repaired_visits += 1

        # Check prescriptions
        query = RecordQuery(
            module_id=schema.PRESCRIPTIONS_MODULE_ID,
            filters=[QueryFilter(field="patient_lookup", operator="eq", value=patient_id)],
            page=1, page_size=100
        )
        prescriptions_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        
        for rx in prescriptions_resp.items:
            rx_doctor = rx.data.get("doctor_lookup")
            if rx_doctor != assigned_doctor:
                print(f"[REPAIR] Prescription {rx.id}: Changing doctor from {rx_doctor} to {assigned_doctor}")
                new_data = rx.data.copy()
                new_data["doctor_lookup"] = assigned_doctor
                HOGC.crud.record.update(UpdateRecordRequest(
                    context=ctx, module_id=schema.PRESCRIPTIONS_MODULE_ID, record_id=rx.id, data=new_data
                ))
                repaired_prescriptions += 1

        # Check laboratory
        query = RecordQuery(
            module_id=schema.LABORATORY_MODULE_ID,
            filters=[QueryFilter(field="patient_lookup", operator="eq", value=patient_id)],
            page=1, page_size=100
        )
        labs_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        
        for lab in labs_resp.items:
            lab_doctor = lab.data.get("doctor_lookup")
            if lab_doctor != assigned_doctor:
                print(f"[REPAIR] Lab {lab.id}: Changing doctor from {lab_doctor} to {assigned_doctor}")
                new_data = lab.data.copy()
                new_data["doctor_lookup"] = assigned_doctor
                HOGC.crud.record.update(UpdateRecordRequest(
                    context=ctx, module_id=schema.LABORATORY_MODULE_ID, record_id=lab.id, data=new_data
                ))
                repaired_labs += 1

    print("\nValidation and Repair Summary:")
    print(f"Repaired Visits: {repaired_visits}")
    print(f"Repaired Prescriptions: {repaired_prescriptions}")
    print(f"Repaired Laboratory Tests: {repaired_labs}")
    print("Complete!")

if __name__ == "__main__":
    with app.app_context():
        # Load schema module IDs before running
        from app.seed.schema import _lookup_module_ids
        _lookup_module_ids()
        
        run_validation_and_repair()

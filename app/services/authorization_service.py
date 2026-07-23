import typing

class AuthorizationService:
    """Service to handle standardized authorization logic."""

    @staticmethod
    def _check_doctor_ownership(user, record, lookup_field: str) -> bool:
        if user.role != "Doctor":
            return True
            
        assigned = record.data.get(lookup_field)
        target_id = user.hogc_record_id
        
        if not assigned or not target_id:
            return False
            
        if isinstance(assigned, list):
            if target_id not in assigned:
                return False
        elif isinstance(assigned, dict):
            if assigned.get("id") != target_id and assigned.get("value") != target_id:
                return False
        else:
            if str(assigned) != str(target_id):
                return False
        return True

    @classmethod
    def can_access_patient(cls, user, patient_record) -> bool:
        if cls._check_doctor_ownership(user, patient_record, "assigned_doctor"):
            return True
            
        if user.role == "Doctor":
            from app.config import Config
            from app.seed import schema
            from hogc.lib import HOGC
            from hogc.lib.base import RequestContext
            from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
            from hogc.lib.contracts.crud.requests import QueryRecordsRequest
            
            user_id = str(user.id) if hasattr(user, "id") and user.id else "system"
            roles = [user.role] if hasattr(user, "role") and user.role else []
            ctx = RequestContext(
                tenant_id=Config.HOGC_TENANT_ID,
                org_id=Config.HOGC_ORG_ID,
                user_id=user_id,
                roles=roles,
            )
            query = RecordQuery(
                module_id=schema.VISITS_MODULE_ID,
                filters=[QueryFilter(field="doctor_lookup", operator="eq", value=user.hogc_record_id)],
                page=1,
                page_size=1000,
            )
            visits_resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
            for v in visits_resp.items:
                if v.data.get("patient_lookup") == patient_record.id:
                    return True
                    
        return False

    @classmethod
    def can_access_visit(cls, user, visit_record) -> bool:
        return cls._check_doctor_ownership(user, visit_record, "doctor_lookup")

    @classmethod
    def can_access_prescription(cls, user, prescription_record) -> bool:
        return cls._check_doctor_ownership(user, prescription_record, "doctor_lookup")

    @classmethod
    def can_access_laboratory(cls, user, lab_record) -> bool:
        return cls._check_doctor_ownership(user, lab_record, "doctor_lookup")

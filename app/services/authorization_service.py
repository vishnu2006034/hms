import typing

class AuthorizationService:
    """Service to handle standardized authorization logic."""

    @staticmethod
    def _check_doctor_ownership(user: typing.Any, record: typing.Any, lookup_field: str) -> bool:
        """Return whether a Doctor user owns the given record via a lookup field.

        Non-Doctor roles always pass (return True).  For Doctors, the method
        checks whether their HOGC record ID appears in the record's lookup
        field value, which may be a list, a dict with an 'id'/'value' key,
        or a plain string.

        Args:
            user: The AuthUser instance to check ownership for.
            record: The HOGC record response object (must have a .data dict).
            lookup_field: The field api_name that stores the assigned user ID
                          (e.g. 'doctor_lookup', 'assigned_doctors').

        Returns:
            True if access is permitted, False if the doctor is not the owner.
        """
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
        """Allow access if the doctor is in the patient's assigned_doctors list, or has a related visit."""
        if user.role != "Doctor":
            return True

        hogc_id = getattr(user, "hogc_record_id", None)
        if hogc_id:
            assigned_raw = patient_record.data.get("assigned_doctors") or ""
            assigned_ids = [i.strip() for i in assigned_raw.split(",") if i.strip()]
            if hogc_id in assigned_ids:
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
    def can_access_visit(cls, user: typing.Any, visit_record: typing.Any) -> bool:
        """Return whether the user may access the given visit record.

        Args:
            user: The AuthUser instance requesting access.
            visit_record: The HOGC visit record response object.

        Returns:
            True if the user is allowed to view or modify the visit.
        """
        return cls._check_doctor_ownership(user, visit_record, "doctor_lookup")

    @classmethod
    def can_access_prescription(cls, user: typing.Any, prescription_record: typing.Any) -> bool:
        """Return whether the user may access the given prescription record.

        Args:
            user: The AuthUser instance requesting access.
            prescription_record: The HOGC prescription record response object.

        Returns:
            True if the user is allowed to view or modify the prescription.
        """
        return cls._check_doctor_ownership(user, prescription_record, "doctor_lookup")

    @classmethod
    def can_access_laboratory(cls, user: typing.Any, lab_record: typing.Any) -> bool:
        """Return whether the user may access the given laboratory record.

        Args:
            user: The AuthUser instance requesting access.
            lab_record: The HOGC laboratory record response object.

        Returns:
            True if the user is allowed to view or modify the lab test.
        """
        return cls._check_doctor_ownership(user, lab_record, "doctor_lookup")

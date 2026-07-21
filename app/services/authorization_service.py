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
        return cls._check_doctor_ownership(user, patient_record, "assigned_doctor")

    @classmethod
    def can_access_visit(cls, user, visit_record) -> bool:
        return cls._check_doctor_ownership(user, visit_record, "doctor_lookup")

    @classmethod
    def can_access_prescription(cls, user, prescription_record) -> bool:
        return cls._check_doctor_ownership(user, prescription_record, "doctor_lookup")

    @classmethod
    def can_access_laboratory(cls, user, lab_record) -> bool:
        return cls._check_doctor_ownership(user, lab_record, "doctor_lookup")

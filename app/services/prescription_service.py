import typing
from app.config import Config
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.services.authorization_service import AuthorizationService
from app.modules.routes_base import (
    _ctx, _get_record, _get_all_records, _resolve_lookups,
    _sync_related_record_on_create, _sync_related_record_on_update,
    _sync_related_record_on_delete, _get_picklist_options
)

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class PrescriptionService:
    """Business service layer for Prescription management using HOGC facade."""

    @staticmethod
    def get_picklists() -> dict[str, list[tuple[str, str]]]:
        """Fetch live picklist options for prescription forms."""
        return _get_picklist_options(schema.PRESCRIPTIONS_MODULE_ID, "frequency", "status")

    @classmethod
    def get_form_context(cls) -> dict[str, typing.Any]:
        """Fetch patients, doctors, and visits for prescription forms."""
        patients = VisibilityService.get_all_patients()
        doctors = [u for u in _get_all_records(schema.USERS_MODULE_ID) if u.data.get("role") == "Doctor"]
        visits = _get_all_records(schema.VISITS_MODULE_ID)
        return {"patients": patients, "doctors": doctors, "visits": visits}

    @classmethod
    def list_prescriptions(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any] | None:
        """Fetch paginated prescriptions list and resolve lookup display names."""
        result = VisibilityService.get_prescriptions(search=search, page=page, page_size=page_size)
        if result is None:
            return None

        prescriptions = result.items
        total = result.total
        total_pages = (total + page_size - 1) // page_size

        resolved = _resolve_lookups(
            prescriptions,
            "patient_lookup", schema.PATIENTS_MODULE_ID,
            "doctor_lookup", schema.USERS_MODULE_ID
        )

        return {
            "prescriptions": prescriptions,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "resolved": resolved,
        }

    @classmethod
    def get_prescription_detail(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch prescription record details with authorization check and resolved lookups."""
        resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_prescription(current_user, resp.data):
            return {"access_denied": True}

        resolved = _resolve_lookups(
            [resp.data],
            "patient_lookup", schema.PATIENTS_MODULE_ID,
            "doctor_lookup", schema.USERS_MODULE_ID,
            "visit_lookup", schema.VISITS_MODULE_ID
        )

        return {
            "prescription": resp.data,
            "resolved": resolved,
        }

    @classmethod
    def create_prescription(cls, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any]:
        """Create a new prescription using HOGC facade and link relationships."""
        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_lookup": form_data.get("visit_lookup", ""),
            "prescribed_date": form_data.get("prescribed_date", ""),
            "medication_name": form_data.get("medication_name", ""),
            "dosage": form_data.get("dosage", ""),
            "frequency": form_data.get("frequency", ""),
            "duration": form_data.get("duration", ""),
            "instructions": form_data.get("instructions", ""),
            "refills": form_data.get("refills", "0"),
            "status": form_data.get("status", "Active"),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, resp.data.id, data)
        return {"prescription": resp.data}

    @classmethod
    def update_prescription(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Update an existing prescription using HOGC facade and sync relationship lookups."""
        resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_prescription(current_user, resp.data):
            return {"access_denied": True}

        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_lookup": form_data.get("visit_lookup", ""),
            "prescribed_date": form_data.get("prescribed_date", ""),
            "medication_name": form_data.get("medication_name", ""),
            "dosage": form_data.get("dosage", ""),
            "frequency": form_data.get("frequency", ""),
            "duration": form_data.get("duration", ""),
            "instructions": form_data.get("instructions", ""),
            "refills": form_data.get("refills", "0"),
            "status": form_data.get("status", "Active"),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        updated = HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_update(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, record_id, old_data, data)
        return {"updated": updated}

    @classmethod
    def delete_prescription(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Delete a prescription using HOGC facade and sync related record deletion."""
        resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_prescription(current_user, resp.data):
            return {"access_denied": True}

        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_delete(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, record_id, old_data)
        HOGC.crud.record.delete(DeleteRecordRequest(
            context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, record_id=record_id
        ))
        return {"success": True}

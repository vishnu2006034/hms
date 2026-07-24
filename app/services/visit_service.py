import typing
from app.config import Config
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.services.authorization_service import AuthorizationService
from app.modules.routes_base import (
    _ctx, _get_record, _get_all_records, _resolve_lookups,
    _sync_related_record_on_create, _sync_related_record_on_update,
    _sync_related_record_on_delete, _get_related_records, _get_picklist_options
)

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class VisitService:
    """Business service layer for Visit management using HOGC facade."""

    @staticmethod
    def get_picklists() -> dict[str, list[tuple[str, str]]]:
        """Fetch live picklist options for the visits form."""
        return _get_picklist_options(schema.VISITS_MODULE_ID, "department", "status", "symptoms")

    @classmethod
    def get_form_context(cls) -> dict[str, typing.Any]:
        """Fetch patient and doctor dropdown options for visit forms."""
        patients = VisibilityService.get_all_patients()
        doctors = [u for u in _get_all_records(schema.USERS_MODULE_ID) if u.data.get("role") == "Doctor"]
        return {"patients": patients, "doctors": doctors}

    @classmethod
    def list_visits(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any] | None:
        """Fetch paginated visits list and resolve related lookup display names."""
        result = VisibilityService.get_visits(search=search, page=page, page_size=page_size)
        if result is None:
            return None

        visits_page = result.items
        total = result.total
        total_pages = (total + page_size - 1) // page_size

        resolved = _resolve_lookups(
            visits_page,
            "patient_lookup", schema.PATIENTS_MODULE_ID,
            "doctor_lookup", schema.USERS_MODULE_ID
        )

        return {
            "visits": visits_page,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "resolved": resolved,
        }

    @classmethod
    def get_visit_detail(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch full visit details, authorized access check, and related lab tests."""
        resp = _get_record(schema.VISITS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_visit(current_user, resp.data):
            return {"access_denied": True}

        resolved = _resolve_lookups(
            [resp.data],
            "patient_lookup", schema.PATIENTS_MODULE_ID,
            "doctor_lookup", schema.USERS_MODULE_ID
        )

        lab_tests: list = []
        if schema.VISITS_LABORATORY_REL_ID:
            try:
                lab_rel = _get_related_records(_ctx(), schema.VISITS_LABORATORY_REL_ID, record_id, page_size=100)
                if lab_rel and lab_rel.items:
                    for link in lab_rel.items:
                        if link.to_record_id:
                            rec = _get_record(schema.LABORATORY_MODULE_ID, link.to_record_id)
                            if rec and rec.data:
                                lab_tests.append(rec.data)
            except Exception:
                pass

        return {
            "visit": resp.data,
            "resolved": resolved,
            "lab_tests": lab_tests,
        }

    @classmethod
    def create_visit(cls, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any]:
        """Create a new visit record using HOGC facade and link relationship."""
        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_date": form_data.get("visit_date", ""),
            "department": form_data.get("department", ""),
            "chief_complaint": form_data.get("chief_complaint", ""),
            "symptoms": ",".join(form_data.getlist("symptoms")) if hasattr(form_data, "getlist") else form_data.get("symptoms", ""),
            "diagnosis": form_data.get("diagnosis", ""),
            "treatment": form_data.get("treatment", ""),
            "vitals_bp": form_data.get("vitals_bp", ""),
            "vitals_temp": form_data.get("vitals_temp", ""),
            "vitals_pulse": form_data.get("vitals_pulse", ""),
            "vitals_weight": form_data.get("vitals_weight", ""),
            "status": form_data.get("status", "Scheduled"),
            "notes": form_data.get("notes", ""),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.VISITS_MODULE_ID, resp.data.id, data)
        return {"visit": resp.data}

    @classmethod
    def update_visit(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Update an existing visit record using HOGC facade and sync updated relations."""
        resp = _get_record(schema.VISITS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_visit(current_user, resp.data):
            return {"access_denied": True}

        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_date": form_data.get("visit_date", ""),
            "department": form_data.get("department", ""),
            "chief_complaint": form_data.get("chief_complaint", ""),
            "symptoms": ",".join(form_data.getlist("symptoms")) if hasattr(form_data, "getlist") else form_data.get("symptoms", ""),
            "diagnosis": form_data.get("diagnosis", ""),
            "treatment": form_data.get("treatment", ""),
            "vitals_bp": form_data.get("vitals_bp", ""),
            "vitals_temp": form_data.get("vitals_temp", ""),
            "vitals_pulse": form_data.get("vitals_pulse", ""),
            "vitals_weight": form_data.get("vitals_weight", ""),
            "status": form_data.get("status", "Scheduled"),
            "notes": form_data.get("notes", ""),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        updated = HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_update(_ctx(), schema.VISITS_MODULE_ID, record_id, old_data, data)
        return {"updated": updated}

    @classmethod
    def delete_visit(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Delete visit record using HOGC facade and sync related record deletion."""
        resp = _get_record(schema.VISITS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_visit(current_user, resp.data):
            return {"access_denied": True}

        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_delete(_ctx(), schema.VISITS_MODULE_ID, record_id, old_data)
        HOGC.crud.record.delete(DeleteRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id
        ))
        return {"success": True}

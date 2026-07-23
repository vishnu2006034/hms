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
from app.services.notifications import notify_lab_result

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class LaboratoryService:
    """Business service layer for Laboratory test management using HOGC facade."""

    @staticmethod
    def get_picklists() -> dict[str, list[tuple[str, str]]]:
        """Fetch live picklist options for lab test forms."""
        return _get_picklist_options(schema.LABORATORY_MODULE_ID, "test_type", "priority", "status")

    @classmethod
    def get_form_context(cls) -> dict[str, typing.Any]:
        """Fetch patients, doctors, technicians, and visits for lab test forms."""
        patients = VisibilityService.get_all_patients()
        all_users = _get_all_records(schema.USERS_MODULE_ID)
        doctors = [u for u in all_users if u.data.get("role") == "Doctor"]
        technicians = all_users
        visits = _get_all_records(schema.VISITS_MODULE_ID)
        return {"patients": patients, "doctors": doctors, "visits": visits, "technicians": technicians}

    @classmethod
    def list_tests(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any] | None:
        """Fetch paginated lab tests list and resolve lookup display names."""
        result = VisibilityService.get_laboratory_tests(search=search, page=page, page_size=page_size)
        if result is None:
            return None

        tests = result.items
        total = result.total
        total_pages = (total + page_size - 1) // page_size

        resolved = _resolve_lookups(tests, "patient_lookup", schema.PATIENTS_MODULE_ID)

        return {
            "tests": tests,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
            "resolved": resolved,
        }

    @classmethod
    def get_test_detail(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch lab test record details with authorization check and resolved lookups."""
        resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_laboratory(current_user, resp.data):
            return {"access_denied": True}

        resolved = _resolve_lookups(
            [resp.data],
            "patient_lookup", schema.PATIENTS_MODULE_ID,
            "doctor_lookup", schema.USERS_MODULE_ID,
            "visit_lookup", schema.VISITS_MODULE_ID,
            "technician_lookup", schema.USERS_MODULE_ID
        )

        return {
            "test": resp.data,
            "resolved": resolved,
        }

    @classmethod
    def create_test(cls, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any]:
        """Create a new lab test using HOGC facade and link relationships."""
        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_lookup": form_data.get("visit_lookup", ""),
            "test_name": form_data.get("test_name", ""),
            "test_type": form_data.get("test_type", ""),
            "priority": form_data.get("priority", "Routine"),
            "sample_date": form_data.get("sample_date", ""),
            "result_date": form_data.get("result_date", ""),
            "result_value": form_data.get("result_value", ""),
            "reference_range": form_data.get("reference_range", ""),
            "status": form_data.get("status", "Ordered"),
            "notes": form_data.get("notes", ""),
            "technician_lookup": form_data.get("technician_lookup", ""),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.LABORATORY_MODULE_ID, resp.data.id, data)
        return {"test": resp.data}

    @classmethod
    def update_test(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Update an existing lab test using HOGC facade and handle notification triggers."""
        resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_laboratory(current_user, resp.data):
            return {"access_denied": True}

        old_status = resp.data.data.get("status") if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else None
        data: dict[str, str] = {
            "patient_lookup": form_data.get("patient_lookup", ""),
            "doctor_lookup": form_data.get("doctor_lookup", ""),
            "visit_lookup": form_data.get("visit_lookup", ""),
            "test_name": form_data.get("test_name", ""),
            "test_type": form_data.get("test_type", ""),
            "priority": form_data.get("priority", "Routine"),
            "sample_date": form_data.get("sample_date", ""),
            "result_date": form_data.get("result_date", ""),
            "result_value": form_data.get("result_value", ""),
            "reference_range": form_data.get("reference_range", ""),
            "status": form_data.get("status", "Ordered"),
            "notes": form_data.get("notes", ""),
            "technician_lookup": form_data.get("technician_lookup", ""),
        }

        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                return {"access_denied": True}
            data["doctor_lookup"] = current_user.hogc_record_id

        updated = HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_update(_ctx(), schema.LABORATORY_MODULE_ID, record_id, old_data, data)

        sent_to = None
        new_status = data.get("status")
        if new_status == "Completed" and old_status != "Completed":
            sent_to = notify_lab_result(data, record_id)

        return {"updated": updated, "sent_to": sent_to}

    @classmethod
    def submit_result(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Submit test results and transition status to Completed."""
        resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_laboratory(current_user, resp.data):
            return {"access_denied": True}

        old_status = resp.data.data.get("status") if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else None
        data = resp.data.data.copy() if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        data.update({
            "result_value": form_data.get("result_value", ""),
            "reference_range": form_data.get("reference_range", ""),
            "result_date": form_data.get("result_date", ""),
            "notes": form_data.get("notes", ""),
            "status": form_data.get("status", "Completed"),
        })

        updated = HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_update(_ctx(), schema.LABORATORY_MODULE_ID, record_id, old_data, data)

        sent_to = None
        new_status = data.get("status")
        if new_status == "Completed" and old_status != "Completed":
            sent_to = notify_lab_result(data, record_id)

        return {"updated": updated, "sent_to": sent_to}

    @classmethod
    def delete_test(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Delete lab test record using HOGC facade and sync related record deletion."""
        resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_laboratory(current_user, resp.data):
            return {"access_denied": True}

        old_data = resp.data.data if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        _sync_related_record_on_delete(_ctx(), schema.LABORATORY_MODULE_ID, record_id, old_data)
        HOGC.crud.record.delete(DeleteRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id
        ))
        return {"success": True}

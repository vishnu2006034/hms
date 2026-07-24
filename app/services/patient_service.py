import typing
from app.config import Config
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.services.authorization_service import AuthorizationService
from app.modules.routes_base import _ctx, _get_record, _get_related_records, _sync_related_record_on_delete, _get_picklist_options

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class PatientService:
    """Business service layer for Managing Patient records and relationships using HOGC facade."""

    @staticmethod
    def get_picklists() -> dict[str, list[tuple[str, str]]]:
        """Fetch live picklist options for patient form."""
        return _get_picklist_options(schema.PATIENTS_MODULE_ID, "gender", "blood_group", "status", "allergies")

    @classmethod
    def list_patients(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any]:
        """Fetch paginated patients list filtered by user visibility and search term."""
        result: typing.Any = VisibilityService.get_patients(search=search, page=page, page_size=page_size)
        patients: list = result.items
        total: int = result.total
        total_pages: int = (total + page_size - 1) // page_size
        return {
            "patients": patients,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
        }

    @classmethod
    def get_patient_detail(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch full patient details along with related visits, prescriptions, and lab tests."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        patient = resp.data
        related_visits: list = []
        related_prescriptions: list = []
        related_lab_tests: list = []
        ctx = _ctx()

        if schema.PATIENTS_VISITS_REL_ID:
            try:
                vr = _get_related_records(ctx, schema.PATIENTS_VISITS_REL_ID, record_id, page_size=50)
                if vr and vr.items:
                    for link in vr.items:
                        rec = _get_record(schema.VISITS_MODULE_ID, link.to_record_id)
                        if rec and rec.data:
                            related_visits.append(rec.data)
            except Exception:
                pass

        if schema.PATIENTS_PRESCRIPTIONS_REL_ID:
            try:
                pr = _get_related_records(ctx, schema.PATIENTS_PRESCRIPTIONS_REL_ID, record_id, page_size=50)
                if pr and pr.items:
                    for link in pr.items:
                        rec = _get_record(schema.PRESCRIPTIONS_MODULE_ID, link.to_record_id)
                        if rec and rec.data:
                            related_prescriptions.append(rec.data)
            except Exception:
                pass

        if schema.PATIENTS_LABORATORY_REL_ID:
            try:
                lr = _get_related_records(ctx, schema.PATIENTS_LABORATORY_REL_ID, record_id, page_size=50)
                if lr and lr.items:
                    for link in lr.items:
                        rec = _get_record(schema.LABORATORY_MODULE_ID, link.to_record_id)
                        if rec and rec.data:
                            related_lab_tests.append(rec.data)
            except Exception:
                pass

        return {
            "patient": patient,
            "related_visits": related_visits,
            "related_prescriptions": related_prescriptions,
            "related_lab_tests": related_lab_tests,
        }

    @classmethod
    def get_patient_for_edit(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch patient record for editing after verifying authorization."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        return {
            "patient": resp.data,
            "picklists": cls.get_picklists(),
        }

    @classmethod
    def create_patient(cls, form_data: dict[str, typing.Any]) -> typing.Any:
        """Create a new patient record using HOGC facade."""
        data: dict[str, str] = {
            "first_name": form_data.get("first_name", ""),
            "last_name": form_data.get("last_name", ""),
            "age": form_data.get("age", ""),
            "date_of_birth": form_data.get("date_of_birth", ""),
            "gender": form_data.get("gender", ""),
            "phone": form_data.get("phone", ""),
            "email": form_data.get("email", ""),
            "address": form_data.get("address", ""),
            "blood_group": form_data.get("blood_group", ""),
            "emergency_contact": form_data.get("emergency_contact", ""),
            "emergency_phone": form_data.get("emergency_phone", ""),
            "insurance_provider": form_data.get("insurance_provider", ""),
            "insurance_id": form_data.get("insurance_id", ""),
            "medical_history": form_data.get("medical_history", ""),
            "allergies": ",".join(form_data.getlist("allergies")) if hasattr(form_data, "getlist") else form_data.get("allergies", ""),
            "status": form_data.get("status", "Active"),
        }
        req = CreateRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, data=data)
        return HOGC.crud.record.create(req)

    @classmethod
    def update_patient(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Update an existing patient record using HOGC facade."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        data: dict[str, str] = {
            "first_name": form_data.get("first_name", ""),
            "last_name": form_data.get("last_name", ""),
            "age": form_data.get("age", ""),
            "date_of_birth": form_data.get("date_of_birth", ""),
            "gender": form_data.get("gender", ""),
            "phone": form_data.get("phone", ""),
            "email": form_data.get("email", ""),
            "address": form_data.get("address", ""),
            "blood_group": form_data.get("blood_group", ""),
            "emergency_contact": form_data.get("emergency_contact", ""),
            "emergency_phone": form_data.get("emergency_phone", ""),
            "insurance_provider": form_data.get("insurance_provider", ""),
            "insurance_id": form_data.get("insurance_id", ""),
            "medical_history": form_data.get("medical_history", ""),
            "allergies": ",".join(form_data.getlist("allergies")) if hasattr(form_data, "getlist") else form_data.get("allergies", ""),
            "status": form_data.get("status", "Active"),
        }
        req = UpdateRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, record_id=record_id, data=data)
        updated = HOGC.crud.record.update(req)
        return {"updated": updated}

    @classmethod
    def delete_patient(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Delete a patient record using HOGC facade and sync related record lookups."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        ctx = _ctx()
        _sync_related_record_on_delete(ctx, schema.PATIENTS_MODULE_ID, record_id)
        req = DeleteRecordRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, record_id=record_id)
        HOGC.crud.record.delete(req)
        return {"success": True}

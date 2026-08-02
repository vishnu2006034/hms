import typing
from app.config import Config
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.services.authorization_service import AuthorizationService
from app.modules.routes_base import (
    _ctx, _get_record, _get_related_records, _link_related_records,
    _unlink_related_records, _sync_related_record_on_delete, _get_picklist_options,
)

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class PatientService:
    """Business service layer for Managing Patient records and relationships using HOGC facade."""

    @classmethod
    def get_doctors(cls) -> list:
        """Fetch users with the Doctor role."""
        from app.services.user_service import UserService
        res = UserService.list_users(page_size=100)
        return [u for u in res.get("users", []) if u.data.get("role") == "Doctor"]

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
        """Fetch full patient details along with related visits, prescriptions, lab tests, and doctors."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        patient = resp.data
        related_visits: list = []
        related_prescriptions: list = []
        related_lab_tests: list = []
        related_doctors: list = []
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

        if schema.PATIENTS_DOCTORS_REL_ID:
            try:
                dr = _get_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, record_id, page_size=50)
                if dr and dr.items:
                    for link in dr.items:
                        rec = _get_record(schema.USERS_MODULE_ID, link.to_record_id)
                        if rec and rec.data:
                            related_doctors.append(rec.data)
            except Exception:
                pass

        return {
            "patient": patient,
            "related_visits": related_visits,
            "related_prescriptions": related_prescriptions,
            "related_lab_tests": related_lab_tests,
            "related_doctors": related_doctors,
        }

    @classmethod
    def get_patient_for_edit(cls, record_id: str, current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Fetch patient record for editing after verifying authorization."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        # Resolve currently linked doctors for pre-selecting checkboxes
        current_doctor_ids: list[str] = []
        if schema.PATIENTS_DOCTORS_REL_ID:
            try:
                ctx = _ctx()
                dr = _get_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, record_id, page_size=50)
                if dr and dr.items:
                    current_doctor_ids = [link.to_record_id for link in dr.items]
            except Exception:
                pass

        return {
            "patient": resp.data,
            "picklists": cls.get_picklists(),
            "current_doctor_ids": current_doctor_ids,
        }

    @classmethod
    def create_patient(cls, form_data: dict[str, typing.Any]) -> typing.Any:
        """Create a new patient record using HOGC facade and link assigned doctors."""
        doctor_ids: list[str] = (
            form_data.getlist("assigned_doctors")
            if hasattr(form_data, "getlist")
            else ([form_data.get("assigned_doctors")] if form_data.get("assigned_doctors") else [])
        )
        raw_data: dict[str, str] = {
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
            "assigned_doctors": ",".join(doctor_ids) if doctor_ids else "",
        }
        data = {k: (v if v != "" else None) for k, v in raw_data.items()}
        ctx = _ctx()
        req = CreateRecordRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, data=data)
        result = HOGC.crud.record.create(req)

        # Link each selected doctor via the many_to_many relationship
        patient_id = result.data.id
        cls._sync_doctor_links(ctx, patient_id, [], doctor_ids)
        return result

    @classmethod
    def update_patient(cls, record_id: str, form_data: dict[str, typing.Any], current_user: typing.Any) -> dict[str, typing.Any] | None:
        """Update an existing patient record using HOGC facade and re-sync doctor links."""
        resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
        if not resp.data:
            return None

        if not AuthorizationService.can_access_patient(current_user, resp.data):
            return {"access_denied": True}

        new_doctor_ids: list[str] = (
            form_data.getlist("assigned_doctors")
            if hasattr(form_data, "getlist")
            else ([form_data.get("assigned_doctors")] if form_data.get("assigned_doctors") else [])
        )

        # Determine previously linked doctors
        old_doctor_ids: list[str] = []
        ctx = _ctx()
        if schema.PATIENTS_DOCTORS_REL_ID:
            try:
                dr = _get_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, record_id, page_size=50)
                if dr and dr.items:
                    old_doctor_ids = [link.to_record_id for link in dr.items]
            except Exception:
                pass

        raw_data: dict[str, str] = {
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
            "assigned_doctors": ",".join(new_doctor_ids) if new_doctor_ids else "",
        }
        data = {k: (v if v != "" else None) for k, v in raw_data.items()}
        req = UpdateRecordRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, record_id=record_id, data=data)
        updated = HOGC.crud.record.update(req)
        cls._sync_doctor_links(ctx, record_id, old_doctor_ids, new_doctor_ids)
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

        # Remove all doctor relationship links before deleting
        if schema.PATIENTS_DOCTORS_REL_ID:
            try:
                dr = _get_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, record_id, page_size=50)
                if dr and dr.items:
                    for link in dr.items:
                        try:
                            _unlink_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, record_id, link.to_record_id)
                        except Exception:
                            pass
            except Exception:
                pass

        _sync_related_record_on_delete(ctx, schema.PATIENTS_MODULE_ID, record_id)
        req = DeleteRecordRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, record_id=record_id)
        HOGC.crud.record.delete(req)
        return {"success": True}

    @staticmethod
    def _sync_doctor_links(ctx: typing.Any, patient_id: str, old_ids: list[str], new_ids: list[str]) -> None:
        """Diff old vs new doctor IDs and create/remove related_record links accordingly."""
        if not schema.PATIENTS_DOCTORS_REL_ID:
            return
        old_set = set(old_ids)
        new_set = set(new_ids)
        for did in new_set - old_set:
            try:
                _link_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, patient_id, did)
            except Exception:
                pass
        for did in old_set - new_set:
            try:
                _unlink_related_records(ctx, schema.PATIENTS_DOCTORS_REL_ID, patient_id, did)
            except Exception:
                pass

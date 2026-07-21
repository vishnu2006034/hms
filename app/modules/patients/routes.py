import typing
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.modules.patients import patients_bp
from app.modules.routes_base import _ctx, _get_record, _get_related_records, _sync_related_record_on_delete, _get_picklist_options
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.services.authorization_service import AuthorizationService

from hogc.lib import HOGC
from hogc.lib.contracts.crud.models import QueryFilter
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


def _patients_picklists() -> dict:
    """Fetch live picklist options for the patients form from the CRUD engine."""
    return _get_picklist_options(schema.PATIENTS_MODULE_ID, "gender", "blood_group", "status")



@patients_bp.route("/")
@login_required
def patients_list() -> typing.Any:
    """Render the paginated list of patients."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")
    
    result: typing.Any = VisibilityService.get_patients(search=search, page=page, page_size=20)
    patients: list = result.items
    total: int = result.total
    total_pages: int = (total + 19) // 20
    
    return render_template(
        "modules/patients/list.html",
        patients=patients, 
        page=page, 
        total_pages=total_pages,
        total=total, 
        search=search
    )


@patients_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE.get("patients", ()))
def patients_create() -> typing.Any:
    """Handle patient creation."""
    if request.method == "POST":
        data: dict[str, str] = {
            "first_name": request.form.get("first_name", ""),
            "last_name": request.form.get("last_name", ""),
            "date_of_birth": request.form.get("date_of_birth", ""),
            "gender": request.form.get("gender", ""),
            "phone": request.form.get("phone", ""),
            "email": request.form.get("email", ""),
            "address": request.form.get("address", ""),
            "blood_group": request.form.get("blood_group", ""),
            "emergency_contact": request.form.get("emergency_contact", ""),
            "emergency_phone": request.form.get("emergency_phone", ""),
            "insurance_provider": request.form.get("insurance_provider", ""),
            "insurance_id": request.form.get("insurance_id", ""),
            "medical_history": request.form.get("medical_history", ""),
            "allergies": request.form.get("allergies", ""),
            "status": request.form.get("status", "Active"),
        }
        req = CreateRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, data=data)
        HOGC.crud.record.create(req)
        
        flash("Patient created successfully!", "success")
        return redirect(url_for("patients.patients_list"))
        
    return render_template("modules/patients/form.html", patient=None, action="create",
                           picklists=_patients_picklists())


@patients_bp.route("/<record_id>")
@login_required
def patients_detail(record_id: str) -> typing.Any:
    """View patient details."""
    resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
    if not resp.data:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.patients_list"))
        
    if not AuthorizationService.can_access_patient(current_user, resp.data):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))
        
    related_visits = []
    related_prescriptions = []
    related_lab_tests = []
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

    return render_template("modules/patients/detail.html", patient=resp.data,
                           related_visits=related_visits,
                           related_prescriptions=related_prescriptions,
                           related_lab_tests=related_lab_tests)


@patients_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT.get("patients", ()))
def patients_edit(record_id: str) -> typing.Any:
    """Handle patient editing."""
    resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
    if not resp.data:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.patients_list"))

    if not AuthorizationService.can_access_patient(current_user, resp.data):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))

    if request.method == "POST":
        data: dict[str, str] = {
            "first_name": request.form.get("first_name", ""),
            "last_name": request.form.get("last_name", ""),
            "date_of_birth": request.form.get("date_of_birth", ""),
            "gender": request.form.get("gender", ""),
            "phone": request.form.get("phone", ""),
            "email": request.form.get("email", ""),
            "address": request.form.get("address", ""),
            "blood_group": request.form.get("blood_group", ""),
            "emergency_contact": request.form.get("emergency_contact", ""),
            "emergency_phone": request.form.get("emergency_phone", ""),
            "insurance_provider": request.form.get("insurance_provider", ""),
            "insurance_id": request.form.get("insurance_id", ""),
            "medical_history": request.form.get("medical_history", ""),
            "allergies": request.form.get("allergies", ""),
            "status": request.form.get("status", "Active"),
        }
        req = UpdateRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, record_id=record_id, data=data)
        HOGC.crud.record.update(req)
        
        flash("Patient updated successfully!", "success")
        return redirect(url_for("patients.patients_detail", record_id=record_id))

    return render_template("modules/patients/form.html", patient=resp.data, action="edit",
                           picklists=_patients_picklists())


@patients_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE.get("patients", ()))
def patients_delete(record_id: str) -> typing.Any:
    """Handle patient deletion."""
    resp = _get_record(schema.PATIENTS_MODULE_ID, record_id)
    if resp.data and not AuthorizationService.can_access_patient(current_user, resp.data):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))

    _sync_related_record_on_delete(_ctx(), schema.PATIENTS_MODULE_ID, record_id)
    req = DeleteRecordRequest(context=_ctx(), module_id=schema.PATIENTS_MODULE_ID, record_id=record_id)
    HOGC.crud.record.delete(req)
    
    flash("Patient deleted.", "success")
    return redirect(url_for("patients.patients_list"))

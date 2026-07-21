from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.modules.prescriptions import prescriptions_bp
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records, _resolve_lookups, _sync_related_record_on_create, _sync_related_record_on_delete
from app.seed import schema
from app.services.authorization_service import AuthorizationService
from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required

from hogc.lib.contracts.crud.models import QueryFilter
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest
from hogc.lib import HOGC


@prescriptions_bp.route("/")
@login_required
def prescriptions_list():
    from app.services.visibility_service import VisibilityService
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    
    result = VisibilityService.get_prescriptions(search=search, page=page, page_size=20)
    if result is None:
        abort(403)
        
    prescriptions = result.items
    total = result.total
    total_pages = (total + 19) // 20
    resolved = _resolve_lookups(prescriptions,
        "patient_lookup", schema.PATIENTS_MODULE_ID,
        "doctor_lookup", schema.USERS_MODULE_ID)
    return render_template("modules/prescriptions/list.html",
                           prescriptions=prescriptions, page=page, total_pages=total_pages,
                           total=total, search=search, resolved=resolved)


def _prescriptions_form_context():
    from app.services.visibility_service import VisibilityService
    patients = VisibilityService.get_all_patients()
    doctors = [u for u in _get_all_records(schema.USERS_MODULE_ID)
               if u.data.get("role") in ("Doctor",)]
    visits = _get_all_records(schema.VISITS_MODULE_ID)
    return {"patients": patients, "doctors": doctors, "visits": visits}


@prescriptions_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE["prescriptions"])
def prescriptions_create():
    if request.method == "POST":
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_lookup": request.form.get("visit_lookup", ""),
            "prescribed_date": request.form.get("prescribed_date", ""),
            "medication_name": request.form.get("medication_name", ""),
            "dosage": request.form.get("dosage", ""),
            "frequency": request.form.get("frequency", ""),
            "duration": request.form.get("duration", ""),
            "instructions": request.form.get("instructions", ""),
            "refills": request.form.get("refills", "0"),
            "status": request.form.get("status", "Active"),
        }
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("prescriptions.prescriptions_list"))
            data["doctor_lookup"] = current_user.hogc_record_id

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, resp.data.id, data)
        flash("Prescription created successfully!", "success")
        return redirect(url_for("prescriptions.prescriptions_list"))
    return render_template("modules/prescriptions/form.html", prescription=None, action="create",
                           **_prescriptions_form_context())


@prescriptions_bp.route("/<record_id>")
@login_required
def prescriptions_detail(record_id):
    resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
    if not resp.data:
        flash("Prescription not found.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))
        
    if not AuthorizationService.can_access_prescription(current_user, resp.data):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))
    resolved = _resolve_lookups([resp.data],
        "patient_lookup", schema.PATIENTS_MODULE_ID,
        "doctor_lookup", schema.USERS_MODULE_ID,
        "visit_lookup", schema.VISITS_MODULE_ID)
    return render_template("modules/prescriptions/detail.html", prescription=resp.data,
                           resolved=resolved)


@prescriptions_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["prescriptions"])
def prescriptions_edit(record_id):
    resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
    if not resp.data:
        flash("Prescription not found.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))
        
    if not AuthorizationService.can_access_prescription(current_user, resp.data):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    if request.method == "POST":
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_lookup": request.form.get("visit_lookup", ""),
            "prescribed_date": request.form.get("prescribed_date", ""),
            "medication_name": request.form.get("medication_name", ""),
            "dosage": request.form.get("dosage", ""),
            "frequency": request.form.get("frequency", ""),
            "duration": request.form.get("duration", ""),
            "instructions": request.form.get("instructions", ""),
            "refills": request.form.get("refills", "0"),
            "status": request.form.get("status", "Active"),
        }
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("prescriptions.prescriptions_list"))
            data["doctor_lookup"] = current_user.hogc_record_id

        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
        from app.modules.routes_base import _sync_related_record_on_update
        _sync_related_record_on_update(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, record_id, old_data, data)
        flash("Prescription updated successfully!", "success")
        return redirect(url_for("prescriptions.prescriptions_detail", record_id=record_id))

    return render_template("modules/prescriptions/form.html", prescription=resp.data, action="edit",
                           **_prescriptions_form_context())


@prescriptions_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["prescriptions"])
def prescriptions_delete(record_id):
    resp = _get_record(schema.PRESCRIPTIONS_MODULE_ID, record_id)
    if resp.data and not AuthorizationService.can_access_prescription(current_user, resp.data):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))
        
    old_data = resp.data.data if resp and resp.data and hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
    _sync_related_record_on_delete(_ctx(), schema.PRESCRIPTIONS_MODULE_ID, record_id, old_data)
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.PRESCRIPTIONS_MODULE_ID, record_id=record_id
    ))
    flash("Prescription deleted.", "success")
    return redirect(url_for("prescriptions.prescriptions_list"))

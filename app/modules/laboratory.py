from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from flask import Blueprint
laboratory_bp = Blueprint("laboratory", __name__, url_prefix="/laboratory")
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records, _resolve_lookups, _sync_related_record_on_create, _sync_related_record_on_delete, _get_picklist_options
from app.seed import schema
from app.services.authorization_service import AuthorizationService
from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required

from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest
from hogc.lib import HOGC


def _laboratory_picklists() -> dict:
    """Fetch live picklist options for the laboratory form from the CRUD engine."""
    return _get_picklist_options(schema.LABORATORY_MODULE_ID, "test_type", "priority", "status")


@laboratory_bp.route("/")
@login_required
def laboratory_list():
    from app.services.visibility_service import VisibilityService
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    
    result = VisibilityService.get_laboratory_tests(search=search, page=page, page_size=20)
    if result is None:
        abort(403)
        
    tests = result.items
    total = result.total
    total_pages = (total + 19) // 20
    resolved = _resolve_lookups(tests,
        "patient_lookup", schema.PATIENTS_MODULE_ID)
    return render_template("modules/laboratory/list.html",
                           tests=tests, page=page, total_pages=total_pages,
                           total=total, search=search, resolved=resolved)


def _laboratory_form_context():
    from app.services.visibility_service import VisibilityService
    patients = VisibilityService.get_all_patients()
    all_users = _get_all_records(schema.USERS_MODULE_ID)
    doctors = [u for u in all_users if u.data.get("role") in ("Doctor",)]
    technicians = all_users
    visits = _get_all_records(schema.VISITS_MODULE_ID)
    return {"patients": patients, "doctors": doctors, "visits": visits, "technicians": technicians}


@laboratory_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE["laboratory"])
def laboratory_create():
    if request.method == "POST":
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_lookup": request.form.get("visit_lookup", ""),
            "test_name": request.form.get("test_name", ""),
            "test_type": request.form.get("test_type", ""),
            "priority": request.form.get("priority", "Routine"),
            "sample_date": request.form.get("sample_date", ""),
            "result_date": request.form.get("result_date", ""),
            "result_value": request.form.get("result_value", ""),
            "reference_range": request.form.get("reference_range", ""),
            "status": request.form.get("status", "Ordered"),
            "notes": request.form.get("notes", ""),
            "technician_lookup": request.form.get("technician_lookup", ""),
        }
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("laboratory.laboratory_list"))
            data["doctor_lookup"] = current_user.hogc_record_id

        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.LABORATORY_MODULE_ID, resp.data.id, data)
        flash("Lab test created successfully!", "success")
        return redirect(url_for("laboratory.laboratory_list"))
    return render_template("modules/laboratory/form.html", test=None, action="create",
                           picklists=_laboratory_picklists(), **_laboratory_form_context())


@laboratory_bp.route("/<record_id>")
@login_required
def laboratory_detail(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
        
    if not AuthorizationService.can_access_laboratory(current_user, resp.data):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
    resolved = _resolve_lookups([resp.data],
        "patient_lookup", schema.PATIENTS_MODULE_ID,
        "doctor_lookup", schema.USERS_MODULE_ID,
        "visit_lookup", schema.VISITS_MODULE_ID,
        "technician_lookup", schema.USERS_MODULE_ID)
    return render_template("modules/laboratory/detail.html", test=resp.data,
                           resolved=resolved)


@laboratory_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["laboratory"])
def laboratory_edit(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
        
    if not AuthorizationService.can_access_laboratory(current_user, resp.data):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        old_status = resp.data.data.get("status") if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else None
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_lookup": request.form.get("visit_lookup", ""),
            "test_name": request.form.get("test_name", ""),
            "test_type": request.form.get("test_type", ""),
            "priority": request.form.get("priority", "Routine"),
            "sample_date": request.form.get("sample_date", ""),
            "result_date": request.form.get("result_date", ""),
            "result_value": request.form.get("result_value", ""),
            "reference_range": request.form.get("reference_range", ""),
            "status": request.form.get("status", "Ordered"),
            "notes": request.form.get("notes", ""),
            "technician_lookup": request.form.get("technician_lookup", ""),
        }
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("laboratory.laboratory_list"))
            data["doctor_lookup"] = current_user.hogc_record_id

        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
        from app.modules.routes_base import _sync_related_record_on_update
        _sync_related_record_on_update(_ctx(), schema.LABORATORY_MODULE_ID, record_id, old_data, data)
        
        new_status = data.get("status")
        if new_status == "Completed" and old_status != "Completed":
            from app.services.notifications import notify_lab_result
            sent_to = notify_lab_result(data, record_id)
            flash(f"Lab test updated successfully! Report sent to: {', '.join(sent_to)}", "success")
        else:
            flash("Lab test updated successfully!", "success")
        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    return render_template("modules/laboratory/form.html", test=resp.data, action="edit",
                           picklists=_laboratory_picklists(), **_laboratory_form_context())


@laboratory_bp.route("/<record_id>/result", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["laboratory"])
def laboratory_result(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
        
    if not AuthorizationService.can_access_laboratory(current_user, resp.data):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        old_status = resp.data.data.get("status") if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else None
        data = resp.data.data.copy() if hasattr(resp.data, "data") and isinstance(resp.data.data, dict) else {}
        data.update({
            "result_value": request.form.get("result_value", ""),
            "reference_range": request.form.get("reference_range", ""),
            "result_date": request.form.get("result_date", ""),
            "status": request.form.get("status", "Completed"),
            "technician_lookup": request.form.get("technician_lookup", ""),
            "notes": request.form.get("notes", "")
        })
        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id, data=data
        ))
        
        new_status = data.get("status")
        if new_status == "Completed" and old_status != "Completed":
            from app.services.notifications import notify_lab_result
            sent_to = notify_lab_result(data, record_id)
            flash(f"Lab test result saved successfully! Report sent to: {', '.join(sent_to)}", "success")
        else:
            flash("Lab test result saved successfully!", "success")
            
        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    return render_template("modules/laboratory/result.html", test=resp.data,
                           picklists=_laboratory_picklists(), **_laboratory_form_context())


@laboratory_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["laboratory"])
def laboratory_delete(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if resp.data and not AuthorizationService.can_access_laboratory(current_user, resp.data):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
        
    old_data = resp.data.data if resp and resp.data and hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
    _sync_related_record_on_delete(_ctx(), schema.LABORATORY_MODULE_ID, record_id, old_data)
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id
    ))
    flash("Lab test deleted.", "success")
    return redirect(url_for("laboratory.laboratory_list"))

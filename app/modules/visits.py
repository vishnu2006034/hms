from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from flask import Blueprint
visits_bp = Blueprint("visits", __name__, url_prefix="/visits")
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records, _resolve_lookups, _sync_related_record_on_create, _sync_related_record_on_delete, _get_related_records, _get_picklist_options
from app.seed import schema
from app.services.authorization_service import AuthorizationService
from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required

from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest, QueryRecordsRequest
from hogc.lib import HOGC


def _visits_picklists() -> dict:
    """Fetch live picklist options for the visits form from the CRUD engine."""
    return _get_picklist_options(schema.VISITS_MODULE_ID, "department", "status")


@visits_bp.route("/")
@login_required
def visits_list():
    from app.services.visibility_service import VisibilityService
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    
    result = VisibilityService.get_visits(search=search, page=page, page_size=20)
    if result is None:
        abort(403)
        
    visits_page = result.items
    total = result.total
    total_pages = (total + 19) // 20

    resolved = _resolve_lookups(visits_page,
        "patient_lookup", schema.PATIENTS_MODULE_ID,
        "doctor_lookup", schema.USERS_MODULE_ID)
    return render_template("modules/visits/list.html",
                           visits=visits_page, page=page, total_pages=total_pages,
                           total=total, search=search, resolved=resolved)


def _visits_form_context():
    from app.services.visibility_service import VisibilityService
    patients = VisibilityService.get_all_patients()
    
    doctors = [u for u in _get_all_records(schema.USERS_MODULE_ID)
               if u.data.get("role") in ("Doctor",)]
    return {"patients": patients, "doctors": doctors}


@visits_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE["visits"])
def visits_create():
    if request.method == "POST":
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_date": request.form.get("visit_date", ""),
            "department": request.form.get("department", ""),
            "chief_complaint": request.form.get("chief_complaint", ""),
            "diagnosis": request.form.get("diagnosis", ""),
            "treatment": request.form.get("treatment", ""),
            "vitals_bp": request.form.get("vitals_bp", ""),
            "vitals_temp": request.form.get("vitals_temp", ""),
            "vitals_pulse": request.form.get("vitals_pulse", ""),
            "vitals_weight": request.form.get("vitals_weight", ""),
            "status": request.form.get("status", "Scheduled"),
            "notes": request.form.get("notes", ""),
        }
        
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("visits.visits_list"))
            # Enforce consistent doctor_lookup
            data["doctor_lookup"] = current_user.hogc_record_id
                
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, data=data
        ))
        _sync_related_record_on_create(_ctx(), schema.VISITS_MODULE_ID, resp.data.id, data)
        flash("Visit created successfully!", "success")
        return redirect(url_for("visits.visits_list"))
    return render_template("modules/visits/form.html", visit=None, action="create",
                           picklists=_visits_picklists(), **_visits_form_context())


@visits_bp.route("/<record_id>")
@login_required
def visits_detail(record_id):
    resp = _get_record(schema.VISITS_MODULE_ID, record_id)
    if not resp.data:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))
        
    if not AuthorizationService.can_access_visit(current_user, resp.data):
        flash("Access denied: You are not assigned to this visit.", "danger")
        return redirect(url_for("visits.visits_list"))
            
    resolved = _resolve_lookups([resp.data],
        "patient_lookup", schema.PATIENTS_MODULE_ID,
        "doctor_lookup", schema.USERS_MODULE_ID)
        
    lab_tests = []
    if schema.VISITS_LABORATORY_REL_ID:
        try:
            lab_rel = _get_related_records(_ctx(), schema.VISITS_LABORATORY_REL_ID, record_id, page_size=100)
            if lab_rel and lab_rel.items:
                lab_ids = [link.to_record_id for link in lab_rel.items]
                for lid in lab_ids:
                    if lid:
                        rec = _get_record(schema.LABORATORY_MODULE_ID, lid)
                        if rec and rec.data:
                            lab_tests.append(rec.data)
        except Exception:
            import traceback
            traceback.print_exc()
        
    return render_template("modules/visits/detail.html", visit=resp.data,
                           resolved=resolved, lab_tests=lab_tests)


@visits_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["visits"])
def visits_edit(record_id):
    resp = _get_record(schema.VISITS_MODULE_ID, record_id)
    if not resp.data:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))
        
    if not AuthorizationService.can_access_visit(current_user, resp.data):
        flash("Access denied: You are not assigned to this visit.", "danger")
        return redirect(url_for("visits.visits_list"))

    if request.method == "POST":
        data = {
            "patient_lookup": request.form.get("patient_lookup", ""),
            "doctor_lookup": request.form.get("doctor_lookup", ""),
            "visit_date": request.form.get("visit_date", ""),
            "department": request.form.get("department", ""),
            "chief_complaint": request.form.get("chief_complaint", ""),
            "diagnosis": request.form.get("diagnosis", ""),
            "treatment": request.form.get("treatment", ""),
            "vitals_bp": request.form.get("vitals_bp", ""),
            "vitals_temp": request.form.get("vitals_temp", ""),
            "vitals_pulse": request.form.get("vitals_pulse", ""),
            "vitals_weight": request.form.get("vitals_weight", ""),
            "status": request.form.get("status", "Scheduled"),
            "notes": request.form.get("notes", ""),
        }
        
        if current_user.role == "Doctor":
            patient_record = _get_record(schema.PATIENTS_MODULE_ID, data["patient_lookup"])
            if patient_record.data and not AuthorizationService.can_access_patient(current_user, patient_record.data):
                flash("Access denied: You are not assigned to this patient.", "danger")
                return redirect(url_for("visits.visits_list"))
            # Enforce consistent doctor_lookup
            data["doctor_lookup"] = current_user.hogc_record_id
                
        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id, data=data
        ))
        old_data = resp.data.data if hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
        from app.modules.routes_base import _sync_related_record_on_update
        _sync_related_record_on_update(_ctx(), schema.VISITS_MODULE_ID, record_id, old_data, data)
        flash("Visit updated successfully!", "success")
        return redirect(url_for("visits.visits_detail", record_id=record_id))

    return render_template("modules/visits/form.html", visit=resp.data, action="edit",
                           picklists=_visits_picklists(), **_visits_form_context())


@visits_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["visits"])
def visits_delete(record_id):
    resp = _get_record(schema.VISITS_MODULE_ID, record_id)
    if resp.data:
        if not AuthorizationService.can_access_visit(current_user, resp.data):
            flash("Access denied: You are not assigned to this visit.", "danger")
            return redirect(url_for("visits.visits_list"))

    old_data = resp.data.data if resp and resp.data and hasattr(resp.data, 'data') and isinstance(resp.data.data, dict) else {}
    _sync_related_record_on_delete(_ctx(), schema.VISITS_MODULE_ID, record_id, old_data)
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id
    ))
    flash("Visit deleted.", "success")
    return redirect(url_for("visits.visits_list"))


from hogc.lib import HOGC
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.modules.visits import visits_bp
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records
from app.seed import schema

from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


@visits_bp.route("/")
@login_required
def visits_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(schema.VISITS_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="chief_complaint")
    visits = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/visits/list.html",
                           visits=visits, page=page, total_pages=total_pages,
                           total=total, search=search)


def _visits_form_context():
    patients = _get_all_records(schema.PATIENTS_MODULE_ID)
    doctors = [u for u in _get_all_records(schema.USERS_MODULE_ID)
               if u.data.get("role") in ("Doctor",)]
    return {"patients": patients, "doctors": doctors}


@visits_bp.route("/create", methods=["GET", "POST"])
@login_required
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
        HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, data=data
        ))
        flash("Visit created successfully!", "success")
        return redirect(url_for("visits.visits_list"))
    return render_template("modules/visits/form.html", visit=None, action="create",
                           **_visits_form_context())


@visits_bp.route("/<record_id>")
@login_required
def visits_detail(record_id):
    resp = _get_record(schema.VISITS_MODULE_ID, record_id)
    if not resp.data:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))
    return render_template("modules/visits/detail.html", visit=resp.data)


@visits_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
def visits_edit(record_id):
    resp = _get_record(schema.VISITS_MODULE_ID, record_id)
    if not resp.data:
        flash("Visit not found.", "danger")
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
        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Visit updated successfully!", "success")
        return redirect(url_for("visits.visits_detail", record_id=record_id))

    return render_template("modules/visits/form.html", visit=resp.data, action="edit",
                           **_visits_form_context())


@visits_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
def visits_delete(record_id):
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.VISITS_MODULE_ID, record_id=record_id
    ))
    flash("Visit deleted.", "success")
    return redirect(url_for("visits.visits_list"))

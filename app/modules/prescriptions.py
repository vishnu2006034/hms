from hogc.lib import HOGC
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.modules.blueprint import modules_bp
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records

import app.modules.seed as seed
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


@modules_bp.route("/prescriptions")
@login_required
def prescriptions_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(seed.PRESCRIPTIONS_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="medication_name")
    prescriptions = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/prescriptions/list.html",
                           prescriptions=prescriptions, page=page, total_pages=total_pages,
                           total=total, search=search)


def _prescriptions_form_context():
    """Fetch patients, doctors, and visits for dropdown selects."""
    patients = _get_all_records(seed.PATIENTS_MODULE_ID)
    doctors = [u for u in _get_all_records(seed.USERS_MODULE_ID)
               if u.data.get("role") in ("Doctor",)]
    visits = _get_all_records(seed.VISITS_MODULE_ID)
    return {"patients": patients, "doctors": doctors, "visits": visits}


@modules_bp.route("/prescriptions/create", methods=["GET", "POST"])
@login_required
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
        HOGC.crud.record.create_record(CreateRecordRequest(
            context=_ctx(), module_id=seed.PRESCRIPTIONS_MODULE_ID, data=data
        ))
        flash("Prescription created successfully!", "success")
        return redirect(url_for("modules.prescriptions_list"))
    return render_template("modules/prescriptions/form.html", prescription=None, action="create",
                           **_prescriptions_form_context())


@modules_bp.route("/prescriptions/<record_id>")
@login_required
def prescriptions_detail(record_id):
    resp = _get_record(seed.PRESCRIPTIONS_MODULE_ID, record_id)
    if not resp.data:
        flash("Prescription not found.", "danger")
        return redirect(url_for("modules.prescriptions_list"))
    return render_template("modules/prescriptions/detail.html", prescription=resp.data)


@modules_bp.route("/prescriptions/<record_id>/edit", methods=["GET", "POST"])
@login_required
def prescriptions_edit(record_id):
    resp = _get_record(seed.PRESCRIPTIONS_MODULE_ID, record_id)
    if not resp.data:
        flash("Prescription not found.", "danger")
        return redirect(url_for("modules.prescriptions_list"))

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
        HOGC.crud.record.update_record(UpdateRecordRequest(
            context=_ctx(), module_id=seed.PRESCRIPTIONS_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Prescription updated successfully!", "success")
        return redirect(url_for("modules.prescriptions_detail", record_id=record_id))

    return render_template("modules/prescriptions/form.html", prescription=resp.data, action="edit",
                           **_prescriptions_form_context())


@modules_bp.route("/prescriptions/<record_id>/delete", methods=["POST"])
@login_required
def prescriptions_delete(record_id):
    HOGC.crud.record.delete_record(DeleteRecordRequest(
        context=_ctx(), module_id=seed.PRESCRIPTIONS_MODULE_ID, record_id=record_id
    ))
    flash("Prescription deleted.", "success")
    return redirect(url_for("modules.prescriptions_list"))

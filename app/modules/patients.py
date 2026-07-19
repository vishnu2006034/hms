from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.modules.blueprint import modules_bp
from app.modules.routes_base import _ctx, _get_records, _get_record
from app.extensions import crud
import app.modules.seed as seed
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest
from hogc.lib import HOGC

@modules_bp.route("/patients")
@login_required
def patients_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(seed.PATIENTS_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="first_name")
    patients = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/patients/list.html",
                           patients=patients, page=page, total_pages=total_pages,
                           total=total, search=search)


@modules_bp.route("/patients/create", methods=["GET", "POST"])
@login_required
def patients_create():
    if request.method == "POST":
        data = {
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
        crud.records.create_record(CreateRecordRequest(
            context=_ctx(), module_id=seed.PATIENTS_MODULE_ID, data=data
        ))
        flash("Patient created successfully!", "success")
        return redirect(url_for("modules.patients_list"))
    return render_template("modules/patients/form.html", patient=None, action="create")


@modules_bp.route("/patients/<record_id>")
@login_required
def patients_detail(record_id):
    resp = _get_record(seed.PATIENTS_MODULE_ID, record_id)
    if not resp.data:
        flash("Patient not found.", "danger")
        return redirect(url_for("modules.patients_list"))
    return render_template("modules/patients/detail.html", patient=resp.data)


@modules_bp.route("/patients/<record_id>/edit", methods=["GET", "POST"])
@login_required
def patients_edit(record_id):
    resp = _get_record(seed.PATIENTS_MODULE_ID, record_id)
    if not resp.data:
        flash("Patient not found.", "danger")
        return redirect(url_for("modules.patients_list"))

    if request.method == "POST":
        data = {
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
        crud.records.update_record(UpdateRecordRequest(
            context=_ctx(), module_id=seed.PATIENTS_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Patient updated successfully!", "success")
        return redirect(url_for("modules.patients_detail", record_id=record_id))

    return render_template("modules/patients/form.html", patient=resp.data, action="edit")


@modules_bp.route("/patients/<record_id>/delete", methods=["POST"])
@login_required
def patients_delete(record_id):
    crud.records.delete_record(DeleteRecordRequest(
        context=_ctx(), module_id=seed.PATIENTS_MODULE_ID, record_id=record_id
    ))
    flash("Patient deleted.", "success")
    return redirect(url_for("modules.patients_list"))

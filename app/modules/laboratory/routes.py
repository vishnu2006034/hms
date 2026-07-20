from hogc.lib import HOGC
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.modules.laboratory import laboratory_bp
from app.modules.routes_base import _ctx, _get_records, _get_record, _get_all_records
from app.seed import schema

from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


@laboratory_bp.route("/")
@login_required
def laboratory_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(schema.LABORATORY_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="test_name")
    tests = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/laboratory/list.html",
                           tests=tests, page=page, total_pages=total_pages,
                           total=total, search=search)


def _laboratory_form_context():
    patients = _get_all_records(schema.PATIENTS_MODULE_ID)
    all_users = _get_all_records(schema.USERS_MODULE_ID)
    doctors = [u for u in all_users if u.data.get("role") in ("Doctor",)]
    technicians = all_users
    visits = _get_all_records(schema.VISITS_MODULE_ID)
    return {"patients": patients, "doctors": doctors, "visits": visits, "technicians": technicians}


@laboratory_bp.route("/create", methods=["GET", "POST"])
@login_required
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
        HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, data=data
        ))
        flash("Lab test created successfully!", "success")
        return redirect(url_for("laboratory.laboratory_list"))
    return render_template("modules/laboratory/form.html", test=None, action="create",
                           **_laboratory_form_context())


@laboratory_bp.route("/<record_id>")
@login_required
def laboratory_detail(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))
    return render_template("modules/laboratory/detail.html", test=resp.data)


@laboratory_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
def laboratory_edit(record_id):
    resp = _get_record(schema.LABORATORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

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
        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Lab test updated successfully!", "success")
        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    return render_template("modules/laboratory/form.html", test=resp.data, action="edit",
                           **_laboratory_form_context())


@laboratory_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
def laboratory_delete(record_id):
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.LABORATORY_MODULE_ID, record_id=record_id
    ))
    flash("Lab test deleted.", "success")
    return redirect(url_for("laboratory.laboratory_list"))

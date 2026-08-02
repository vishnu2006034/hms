import typing
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.patient_service import PatientService
from app.modules.routes_base import get_module_metadata
from app.seed import schema

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patients_bp.route("/")
@login_required
def patients_list() -> typing.Any:
    """Render the paginated list of patients."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] = PatientService.list_patients(search=search, page=page, page_size=20)
    return render_template(
        "modules/patients/list.html",
        patients=result["patients"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"]
    )


@patients_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE.get("patients", ()))
def patients_create() -> typing.Any:
    """Handle patient creation."""
    if request.method == "POST":
        PatientService.create_patient(request.form)
        flash("Patient created successfully!", "success")
        return redirect(url_for("patients.patients_list"))

    meta = get_module_metadata(schema.PATIENTS_MODULE_ID)
    doctors = PatientService.get_doctors()
    lookup_data = {"assigned_doctors": [(d.id, d.data.get("full_name", "")) for d in doctors]}
    return render_template(
        "modules/patients/form.html",
        patient=None,
        record=None,
        action="create",
        lookup_data=lookup_data,
        current_doctor_ids=[],
        **meta
    )


@patients_bp.route("/<record_id>")
@login_required
def patients_detail(record_id: str) -> typing.Any:
    """View patient details."""
    detail: dict[str, typing.Any] | None = PatientService.get_patient_detail(record_id, current_user)
    if detail is None:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.patients_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))

    meta = get_module_metadata(schema.PATIENTS_MODULE_ID)
    doctors = PatientService.get_doctors()
    lookup_data = {"assigned_doctors": [(d.id, d.data.get("full_name", "")) for d in doctors]}
    return render_template(
        "modules/patients/detail.html",
        patient=detail["patient"],
        record=detail["patient"],
        related_visits=detail["related_visits"],
        related_prescriptions=detail["related_prescriptions"],
        related_lab_tests=detail["related_lab_tests"],
        related_doctors=detail["related_doctors"],
        lookup_data=lookup_data,
        **meta
    )


@patients_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT.get("patients", ()))
def patients_edit(record_id: str) -> typing.Any:
    """Handle patient editing."""
    edit_data: dict[str, typing.Any] | None = PatientService.get_patient_for_edit(record_id, current_user)
    if edit_data is None:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.patients_list"))

    if edit_data.get("access_denied"):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = PatientService.update_patient(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("patients.patients_list"))

        flash("Patient updated successfully!", "success")
        return redirect(url_for("patients.patients_detail", record_id=record_id))

    meta = get_module_metadata(schema.PATIENTS_MODULE_ID)
    doctors = PatientService.get_doctors()
    lookup_data = {"assigned_doctors": [(d.id, d.data.get("full_name", "")) for d in doctors]}
    return render_template(
        "modules/patients/form.html",
        patient=edit_data["patient"],
        record=edit_data["patient"],
        action="edit",
        lookup_data=lookup_data,
        current_doctor_ids=edit_data.get("current_doctor_ids", []),
        **meta
    )


@patients_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE.get("patients", ()))
def patients_delete(record_id: str) -> typing.Any:
    """Handle patient deletion."""
    result: dict[str, typing.Any] | None = PatientService.delete_patient(record_id, current_user)
    if result is None:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients.patients_list"))

    if result.get("access_denied"):
        flash("Access denied: You are not assigned to this patient.", "danger")
        return redirect(url_for("patients.patients_list"))

    flash("Patient deleted.", "success")
    return redirect(url_for("patients.patients_list"))

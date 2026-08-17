import typing
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.prescription_service import PrescriptionService
from app.modules.routes_base import get_module_metadata
from app.seed import schema

prescriptions_bp = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")


@prescriptions_bp.route("/")
@login_required
def prescriptions_list() -> typing.Any:
    """Render paginated list of prescriptions."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] | None = PrescriptionService.list_prescriptions(search=search, page=page, page_size=20)
    if result is None:
        abort(403)

    return render_template(
        "modules/prescriptions/list.html",
        prescriptions=result["prescriptions"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"],
        resolved=result["resolved"]
    )


def _build_lookup_data(form_ctx: dict) -> dict:
    """Build the lookup_data dict consumed by the prescription form template.

    Converts each list of HOGC record objects in form_ctx into a list of
    (record_id, display_label) tuples that can be rendered as <select> options.

    Args:
        form_ctx: Dict returned by PrescriptionService.get_form_context(), containing
                  'patients', 'doctors', and 'visits' record lists.

    Returns:
        A dict mapping each lookup field api_name to its list of (id, label) tuples.
    """
    return {
        "patient_lookup": [(p.id, f"{p.data.get('first_name', '')} {p.data.get('last_name', '')} — {p.data.get('phone', '')}") for p in form_ctx.get("patients", [])],
        "doctor_lookup": [(d.id, f"{d.data.get('full_name', '')} — {d.data.get('department', '')}") for d in form_ctx.get("doctors", [])],
        "visit_lookup": [(v.id, f"{v.data.get('visit_date', '')[:10]} — {v.data.get('chief_complaint', '')[:40]}") for v in form_ctx.get("visits", [])]
    }


@prescriptions_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE.get("prescriptions", ()))
def prescriptions_create() -> typing.Any:
    """Handle prescription creation."""
    if request.method == "POST":
        res: dict[str, typing.Any] = PrescriptionService.create_prescription(request.form, current_user)
        if res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("prescriptions.prescriptions_list"))

        flash("Prescription created successfully!", "success")
        return redirect(url_for("prescriptions.prescriptions_list"))

    form_ctx: dict[str, typing.Any] = PrescriptionService.get_form_context()
    meta = get_module_metadata(schema.PRESCRIPTIONS_MODULE_ID)
    return render_template(
        "modules/prescriptions/form.html",
        prescription=None,
        record=None,
        action="create",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@prescriptions_bp.route("/<record_id>")
@login_required
def prescriptions_detail(record_id: str) -> typing.Any:
    """View prescription details."""
    detail: dict[str, typing.Any] | None = PrescriptionService.get_prescription_detail(record_id, current_user)
    if detail is None:
        flash("Prescription not found.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    resolved = detail.get("resolved", {})
    presc_resolved = resolved.get(record_id, {})
    lookup_data = {
        k: {detail["prescription"].get(k): v} for k, v in presc_resolved.items() if detail["prescription"].get(k)
    }

    meta = get_module_metadata(schema.PRESCRIPTIONS_MODULE_ID)
    return render_template(
        "modules/prescriptions/detail.html",
        prescription=detail["prescription"],
        record=detail["prescription"],
        resolved=resolved,
        lookup_data=lookup_data,
        **meta
    )


@prescriptions_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT.get("prescriptions", ()))
def prescriptions_edit(record_id: str) -> typing.Any:
    """Handle prescription editing."""
    detail: dict[str, typing.Any] | None = PrescriptionService.get_prescription_detail(record_id, current_user)
    if detail is None:
        flash("Prescription not found.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = PrescriptionService.update_prescription(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("prescriptions.prescriptions_list"))

        flash("Prescription updated successfully!", "success")
        return redirect(url_for("prescriptions.prescriptions_detail", record_id=record_id))

    form_ctx: dict[str, typing.Any] = PrescriptionService.get_form_context()
    meta = get_module_metadata(schema.PRESCRIPTIONS_MODULE_ID)
    return render_template(
        "modules/prescriptions/form.html",
        prescription=detail["prescription"],
        record=detail["prescription"],
        action="edit",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@prescriptions_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["prescriptions"])
def prescriptions_delete(record_id: str) -> typing.Any:
    """Handle prescription deletion."""
    res: dict[str, typing.Any] | None = PrescriptionService.delete_prescription(record_id, current_user)
    if res is None:
        flash("Prescription not found.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    if res.get("access_denied"):
        flash("Access denied: You are not assigned to this prescription.", "danger")
        return redirect(url_for("prescriptions.prescriptions_list"))

    flash("Prescription deleted.", "success")
    return redirect(url_for("prescriptions.prescriptions_list"))

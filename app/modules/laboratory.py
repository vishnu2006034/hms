import typing
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.laboratory_service import LaboratoryService
from app.modules.routes_base import get_module_metadata
from app.seed import schema

laboratory_bp = Blueprint("laboratory", __name__, url_prefix="/laboratory")


@laboratory_bp.route("/")
@login_required
def laboratory_list() -> typing.Any:
    """Render paginated list of lab tests."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] | None = LaboratoryService.list_tests(search=search, page=page, page_size=20)
    if result is None:
        abort(403)

    return render_template(
        "modules/laboratory/list.html",
        tests=result["tests"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"],
        resolved=result["resolved"]
    )


def _build_lookup_data(form_ctx: dict) -> dict:
    """Build the lookup_data dict consumed by the lab test form template.

    Converts each list of HOGC record objects in form_ctx into a list of
    (record_id, display_label) tuples that can be rendered as <select> options.

    Args:
        form_ctx: Dict returned by LaboratoryService.get_form_context(), containing
                  'patients', 'doctors', 'visits', and 'technicians' record lists.

    Returns:
        A dict mapping each lookup field api_name to its list of (id, label) tuples.
    """
    return {
        "patient_lookup": [(p.id, f"{p.data.get('first_name', '')} {p.data.get('last_name', '')} — {p.data.get('phone', '')}") for p in form_ctx.get("patients", [])],
        "doctor_lookup": [(d.id, f"{d.data.get('full_name', '')} — {d.data.get('department', '')}") for d in form_ctx.get("doctors", [])],
        "visit_lookup": [(v.id, f"{v.data.get('visit_date', '')[:10]} — {v.data.get('chief_complaint', '')[:40]}") for v in form_ctx.get("visits", [])],
        "technician_lookup": [(t.id, f"{t.data.get('full_name', '')} — {t.data.get('role', '')}") for t in form_ctx.get("technicians", [])]
    }


@laboratory_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE.get("laboratory", ()))
def laboratory_create() -> typing.Any:
    """Handle lab test creation."""
    if request.method == "POST":
        res: dict[str, typing.Any] = LaboratoryService.create_test(request.form, current_user)
        if res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        flash("Lab Test created successfully!", "success")
        return redirect(url_for("laboratory.laboratory_list"))

    form_ctx: dict[str, typing.Any] = LaboratoryService.get_form_context()
    meta = get_module_metadata(schema.LABORATORY_MODULE_ID)
    return render_template(
        "modules/laboratory/form.html",
        test=None,
        record=None,
        action="create",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@laboratory_bp.route("/<record_id>")
@login_required
def laboratory_detail(record_id: str) -> typing.Any:
    """View lab test details."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    resolved = detail.get("resolved", {})
    test_resolved = resolved.get(record_id, {})
    lookup_data = {
        k: {detail["test"].get(k): v} for k, v in test_resolved.items() if detail["test"].get(k)
    }

    meta = get_module_metadata(schema.LABORATORY_MODULE_ID)
    return render_template(
        "modules/laboratory/detail.html",
        test=detail["test"],
        record=detail["test"],
        resolved=resolved,
        lookup_data=lookup_data,
        **meta
    )


@laboratory_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT.get("laboratory", ()))
def laboratory_edit(record_id: str) -> typing.Any:
    """Handle lab test editing."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = LaboratoryService.update_test(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        if res and res.get("sent_to"):
            flash(f"Test updated successfully! Email notification sent to {res['sent_to']}", "success")
        else:
            flash("Test updated successfully!", "success")

        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    form_ctx: dict[str, typing.Any] = LaboratoryService.get_form_context()
    meta = get_module_metadata(schema.LABORATORY_MODULE_ID)
    return render_template(
        "modules/laboratory/form.html",
        test=detail["test"],
        record=detail["test"],
        action="edit",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@laboratory_bp.route("/<record_id>/result", methods=["GET", "POST"])
@login_required
@role_required('Admin', 'Technician')
def laboratory_result(record_id: str) -> typing.Any:
    """Submit test results (specialized view)."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = LaboratoryService.submit_result(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        if res and res.get("sent_to"):
            flash(f"Results submitted! Email notification sent to {res['sent_to']}", "success")
        else:
            flash("Results submitted successfully!", "success")

        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    resolved = detail.get("resolved", {})
    test_resolved = resolved.get(record_id, {})
    lookup_data = {
        k: {detail["test"].get(k): v} for k, v in test_resolved.items() if detail["test"].get(k)
    }

    meta = get_module_metadata(schema.LABORATORY_MODULE_ID)
    return render_template(
        "modules/laboratory/result.html",
        test=detail["test"],
        record=detail["test"],
        resolved=resolved,
        lookup_data=lookup_data,
        **meta
    )


@laboratory_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["laboratory"])
def laboratory_delete(record_id: str) -> typing.Any:
    """Handle lab test deletion."""
    res: dict[str, typing.Any] | None = LaboratoryService.delete_test(record_id, current_user)
    if res is None:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if res.get("access_denied"):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    flash("Lab test deleted.", "success")
    return redirect(url_for("laboratory.laboratory_list"))

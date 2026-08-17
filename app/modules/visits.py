import typing
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.visit_service import VisitService
from app.modules.routes_base import get_module_metadata
from app.seed import schema

visits_bp = Blueprint("visits", __name__, url_prefix="/visits")


@visits_bp.route("/")
@login_required
def visits_list() -> typing.Any:
    """Render paginated list of visits."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] | None = VisitService.list_visits(search=search, page=page, page_size=20)
    if result is None:
        abort(403)

    return render_template(
        "modules/visits/list.html",
        visits=result["visits"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"],
        resolved=result["resolved"]
    )


def _build_lookup_data(form_ctx: dict) -> dict:
    """Build the lookup_data dict consumed by the visit form template.

    Converts each list of HOGC record objects in form_ctx into a list of
    (record_id, display_label) tuples that can be rendered as <select> options.

    Args:
        form_ctx: Dict returned by VisitService.get_form_context(), containing
                  'patients' and 'doctors' record lists.

    Returns:
        A dict mapping each lookup field api_name to its list of (id, label) tuples.
    """
    return {
        "patient_lookup": [(p.id, f"{p.data.get('first_name', '')} {p.data.get('last_name', '')} — {p.data.get('phone', '')}") for p in form_ctx.get("patients", [])],
        "doctor_lookup": [(d.id, f"{d.data.get('full_name', '')} — {d.data.get('department', '')}") for d in form_ctx.get("doctors", [])]
    }


@visits_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE.get("visits", ()))
def visits_create() -> typing.Any:
    """Handle visit creation."""
    if request.method == "POST":
        res: dict[str, typing.Any] = VisitService.create_visit(request.form, current_user)
        if res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("visits.visits_list"))

        flash("Visit created successfully!", "success")
        return redirect(url_for("visits.visits_list"))

    form_ctx: dict[str, typing.Any] = VisitService.get_form_context()
    meta = get_module_metadata(schema.VISITS_MODULE_ID)
    return render_template(
        "modules/visits/form.html",
        visit=None,
        record=None,
        action="create",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@visits_bp.route("/<record_id>")
@login_required
def visits_detail(record_id: str) -> typing.Any:
    """View visit details."""
    detail: dict[str, typing.Any] | None = VisitService.get_visit_detail(record_id, current_user)
    if detail is None:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this visit.", "danger")
        return redirect(url_for("visits.visits_list"))

    resolved = detail.get("resolved", {})
    visit_resolved = resolved.get(record_id, {})
    lookup_data = {
        k: {detail["visit"].get(k): v} for k, v in visit_resolved.items() if detail["visit"].get(k)
    }

    meta = get_module_metadata(schema.VISITS_MODULE_ID)
    return render_template(
        "modules/visits/detail.html",
        visit=detail["visit"],
        record=detail["visit"],
        resolved=resolved,
        lab_tests=detail["lab_tests"],
        lookup_data=lookup_data,
        **meta
    )


@visits_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT.get("visits", ()))
def visits_edit(record_id: str) -> typing.Any:
    """Handle visit editing."""
    detail: dict[str, typing.Any] | None = VisitService.get_visit_detail(record_id, current_user)
    if detail is None:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this visit.", "danger")
        return redirect(url_for("visits.visits_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = VisitService.update_visit(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("visits.visits_list"))

        flash("Visit updated successfully!", "success")
        return redirect(url_for("visits.visits_detail", record_id=record_id))

    form_ctx: dict[str, typing.Any] = VisitService.get_form_context()
    meta = get_module_metadata(schema.VISITS_MODULE_ID)
    return render_template(
        "modules/visits/form.html",
        visit=detail["visit"],
        record=detail["visit"],
        action="edit",
        lookup_data=_build_lookup_data(form_ctx),
        **meta
    )


@visits_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["visits"])
def visits_delete(record_id: str) -> typing.Any:
    """Handle visit deletion."""
    res: dict[str, typing.Any] | None = VisitService.delete_visit(record_id, current_user)
    if res is None:
        flash("Visit not found.", "danger")
        return redirect(url_for("visits.visits_list"))

    if res.get("access_denied"):
        flash("Access denied: You are not assigned to this visit.", "danger")
        return redirect(url_for("visits.visits_list"))

    flash("Visit deleted.", "success")
    return redirect(url_for("visits.visits_list"))

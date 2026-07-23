import typing
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_required, current_user

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.laboratory_service import LaboratoryService

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


@laboratory_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE["laboratory"])
def laboratory_create() -> typing.Any:
    """Handle lab test creation."""
    if request.method == "POST":
        res: dict[str, typing.Any] = LaboratoryService.create_test(request.form, current_user)
        if res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        flash("Lab test created successfully!", "success")
        return redirect(url_for("laboratory.laboratory_list"))

    form_ctx: dict[str, typing.Any] = LaboratoryService.get_form_context()
    return render_template(
        "modules/laboratory/form.html",
        test=None,
        action="create",
        picklists=LaboratoryService.get_picklists(),
        **form_ctx
    )


@laboratory_bp.route("/<record_id>")
@login_required
def laboratory_detail(record_id: str) -> typing.Any:
    """View lab test details."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    return render_template(
        "modules/laboratory/detail.html",
        test=detail["test"],
        resolved=detail["resolved"]
    )


@laboratory_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["laboratory"])
def laboratory_edit(record_id: str) -> typing.Any:
    """Handle lab test editing."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = LaboratoryService.update_test(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this patient.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        if res and res.get("sent_to"):
            flash(f"Lab test updated successfully! Report sent to: {', '.join(res['sent_to'])}", "success")
        else:
            flash("Lab test updated successfully!", "success")

        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    form_ctx: dict[str, typing.Any] = LaboratoryService.get_form_context()
    return render_template(
        "modules/laboratory/form.html",
        test=detail["test"],
        action="edit",
        picklists=LaboratoryService.get_picklists(),
        **form_ctx
    )


@laboratory_bp.route("/<record_id>/result", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["laboratory"])
def laboratory_result(record_id: str) -> typing.Any:
    """Submit test result and update status."""
    detail: dict[str, typing.Any] | None = LaboratoryService.get_test_detail(record_id, current_user)
    if detail is None:
        flash("Lab test not found.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if detail.get("access_denied"):
        flash("Access denied: You are not assigned to this lab test.", "danger")
        return redirect(url_for("laboratory.laboratory_list"))

    if request.method == "POST":
        res: dict[str, typing.Any] | None = LaboratoryService.submit_result(record_id, request.form, current_user)
        if res and res.get("access_denied"):
            flash("Access denied: You are not assigned to this lab test.", "danger")
            return redirect(url_for("laboratory.laboratory_list"))

        if res and res.get("sent_to"):
            flash(f"Lab test result recorded! Report sent to: {', '.join(res['sent_to'])}", "success")
        else:
            flash("Lab test result recorded successfully!", "success")

        return redirect(url_for("laboratory.laboratory_detail", record_id=record_id))

    return render_template(
        "modules/laboratory/result_form.html",
        test=detail["test"],
        resolved=detail["resolved"]
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

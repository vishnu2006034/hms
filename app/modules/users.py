import typing
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required

from app.auth.utils import admin_required
from app.services.user_service import UserService

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
@login_required
@admin_required
def users_list() -> typing.Any:
    """Render paginated list of staff users."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] = UserService.list_users(search=search, page=page, page_size=20)
    return render_template(
        "modules/users/list.html",
        users=result["users"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"]
    )


@users_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def users_create() -> typing.Any:
    """Handle staff user creation."""
    if request.method == "POST":
        UserService.create_user(request.form)
        flash("Staff member created successfully!", "success")
        return redirect(url_for("users.users_list"))

    return render_template("modules/users/form.html", user=None, action="create")


@users_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def users_edit(record_id: str) -> typing.Any:
    """Handle staff user editing."""
    detail: dict[str, typing.Any] | None = UserService.get_user_detail(record_id)
    if detail is None:
        flash("User not found.", "danger")
        return redirect(url_for("users.users_list"))

    if request.method == "POST":
        UserService.update_user(record_id, request.form)
        flash("Staff member updated successfully!", "success")
        return redirect(url_for("users.users_list"))

    return render_template("modules/users/form.html", user=detail["user"], action="edit")


@users_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@admin_required
def users_delete(record_id: str) -> typing.Any:
    """Handle staff user deletion."""
    UserService.delete_user(record_id)
    flash("Staff member deleted.", "success")
    return redirect(url_for("users.users_list"))

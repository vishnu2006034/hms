from hogc.lib import HOGC
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from flask import Blueprint
users_bp = Blueprint("users", __name__, url_prefix="/users")
from app.modules.routes_base import _ctx, _get_records, _get_record, _sync_related_record_on_delete
from app.extensions import db
from app.seed import schema
from app.auth.models import AuthUser
from app.auth.utils import admin_required
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


@users_bp.route("/")
@login_required
@admin_required
def users_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(schema.USERS_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="full_name")
    users = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/users/list.html",
                           users=users, page=page, total_pages=total_pages,
                           total=total, search=search)


@users_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def users_create():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        full_name = request.form.get("full_name", "")
        role = request.form.get("role", "Doctor")
        password = request.form.get("password", "password123")

        auth_user = AuthUser(username=username, email=email, full_name=full_name, role=role)
        auth_user.set_password(password)
        db.session.add(auth_user)
        db.session.commit()

        data = {
            "full_name": full_name,
            "email": email,
            "phone": request.form.get("phone", ""),
            "role": role,
            "department": request.form.get("department", ""),
            "is_active": "true",
        }
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.USERS_MODULE_ID, data=data
        ))
        auth_user.hogc_record_id = resp.data.id
        db.session.commit()

        flash("Staff member created successfully!", "success")
        return redirect(url_for("users.users_list"))
    return render_template("modules/users/form.html", user=None, action="create")


@users_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def users_edit(record_id):
    resp = _get_record(schema.USERS_MODULE_ID, record_id)
    if not resp.data:
        flash("User not found.", "danger")
        return redirect(url_for("users.users_list"))

    if request.method == "POST":
        data = {
            "full_name": request.form.get("full_name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "role": request.form.get("role", ""),
            "department": request.form.get("department", ""),
            "is_active": request.form.get("is_active", "true"),
        }
        HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.USERS_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Staff member updated successfully!", "success")
        return redirect(url_for("users.users_list"))

    return render_template("modules/users/form.html", user=resp.data, action="edit")


@users_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@admin_required
def users_delete(record_id):
    _sync_related_record_on_delete(_ctx(), schema.USERS_MODULE_ID, record_id)
    HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=schema.USERS_MODULE_ID, record_id=record_id
    ))
    flash("Staff member deleted.", "success")
    return redirect(url_for("users.users_list"))

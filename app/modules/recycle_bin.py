import typing
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListModulesRequest
from app.auth.utils import role_required
from app.modules.routes_base import (
    _ctx,
    _get_deleted_records,
    _restore_record,
    _permanent_delete_record,
    _get_display_name_from_data,
)

recycle_bin_bp = Blueprint("recycle_bin", __name__, url_prefix="/recycle_bin")

def _get_modules() -> list:
    """Fetch all modules to display in the dropdown."""
    ctx = _ctx()
    resp = HOGC.crud.module.list(ListModulesRequest(context=ctx, page=1, page_size=50))
    return resp.items if resp and resp.items else []

@recycle_bin_bp.route("/")
@login_required
@role_required("Admin")
def list_deleted() -> typing.Any:
    """List deleted records for a selected module."""
    modules = _get_modules()
    if not modules:
        flash("No modules available.", "warning")
        return render_template("modules/recycle_bin/list.html", records=[], modules=[], current_module_id=None)

    # Use patients module as default if none specified
    default_module_id = next((m.id for m in modules if m.api_name == "patients"), modules[0].id)
    module_id = request.args.get("module_id", default_module_id)
    
    current_module = next((m for m in modules if m.id == module_id), None)
    if not current_module:
        flash("Invalid module selected.", "danger")
        return redirect(url_for("recycle_bin.list_deleted"))

    page = request.args.get("page", 1, type=int)
    page_size = 20

    try:
        resp = _get_deleted_records(module_id=module_id, page=page, page_size=page_size)
        records = resp.items if resp and resp.items else []
        total = resp.total if resp else 0
        total_pages = (total + page_size - 1) // page_size

        # Enhance records with a display name for the UI
        display_records = []
        for r in records:
            display_name = _get_display_name_from_data(r.data, r.id)
            deleted_at = getattr(r, "deleted_at", r.updated_at)
            
            if hasattr(deleted_at, "strftime"):
                deleted_at_str = deleted_at.strftime("%Y-%m-%d %H:%M")
            else:
                deleted_at_str = str(deleted_at)
                
            display_records.append({
                "id": r.id,
                "display_name": display_name,
                "data": r.data,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "deleted_at": deleted_at_str,
            })
            
        return render_template(
            "modules/recycle_bin/list.html",
            records=display_records,
            modules=modules,
            current_module=current_module,
            page=page,
            total_pages=total_pages,
            total=total,
        )
    except Exception as e:
        flash(f"Error fetching deleted records: {e}", "danger")
        return render_template(
            "modules/recycle_bin/list.html", 
            records=[], 
            modules=modules, 
            current_module=current_module,
            page=1,
            total_pages=0,
            total=0
        )

@recycle_bin_bp.route("/<module_id>/<record_id>/restore", methods=["POST"])
@login_required
@role_required("Admin")
def restore(module_id: str, record_id: str) -> typing.Any:
    """Restore a deleted record."""
    try:
        _restore_record(module_id, record_id)
        flash("Record restored successfully.", "success")
    except Exception as e:
        flash(f"Failed to restore record: {e}", "danger")
    return redirect(url_for("recycle_bin.list_deleted", module_id=module_id))

@recycle_bin_bp.route("/<module_id>/<record_id>/permanent_delete", methods=["POST"])
@login_required
@role_required("Admin")
def permanent_delete(module_id: str, record_id: str) -> typing.Any:
    """Permanently delete a record."""
    try:
        _permanent_delete_record(module_id, record_id)
        flash("Record permanently deleted.", "success")
    except Exception as e:
        flash(f"Failed to permanently delete record: {e}", "danger")
    return redirect(url_for("recycle_bin.list_deleted", module_id=module_id))

from hogc.lib import HOGC
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.modules.blueprint import modules_bp
from app.modules.routes_base import _ctx, _get_records, _get_record

import app.modules.seed as seed
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


@modules_bp.route("/inventory")
@login_required
def inventory_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    result = _get_records(seed.INVENTORY_MODULE_ID, page=page, page_size=20,
                          search=search, search_field="item_name")
    items = result.items
    total = result.total
    total_pages = (total + 19) // 20
    return render_template("modules/inventory/list.html",
                           items=items, page=page, total_pages=total_pages,
                           total=total, search=search)


@modules_bp.route("/inventory/create", methods=["GET", "POST"])
@login_required
def inventory_create():
    if request.method == "POST":
        data = {
            "item_name": request.form.get("item_name", ""),
            "category": request.form.get("category", ""),
            "description": request.form.get("description", ""),
            "quantity": request.form.get("quantity", "0"),
            "unit": request.form.get("unit", ""),
            "unit_price": request.form.get("unit_price", "0"),
            "supplier": request.form.get("supplier", ""),
            "reorder_level": request.form.get("reorder_level", "0"),
            "expiry_date": request.form.get("expiry_date", ""),
            "batch_number": request.form.get("batch_number", ""),
            "location": request.form.get("location", ""),
            "status": request.form.get("status", "In-Stock"),
        }
        HOGC.crud.record.create_record(CreateRecordRequest(
            context=_ctx(), module_id=seed.INVENTORY_MODULE_ID, data=data
        ))
        flash("Inventory item created successfully!", "success")
        return redirect(url_for("modules.inventory_list"))
    return render_template("modules/inventory/form.html", item=None, action="create")


@modules_bp.route("/inventory/<record_id>")
@login_required
def inventory_detail(record_id):
    resp = _get_record(seed.INVENTORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Item not found.", "danger")
        return redirect(url_for("modules.inventory_list"))
    return render_template("modules/inventory/detail.html", item=resp.data)


@modules_bp.route("/inventory/<record_id>/edit", methods=["GET", "POST"])
@login_required
def inventory_edit(record_id):
    resp = _get_record(seed.INVENTORY_MODULE_ID, record_id)
    if not resp.data:
        flash("Item not found.", "danger")
        return redirect(url_for("modules.inventory_list"))

    if request.method == "POST":
        data = {
            "item_name": request.form.get("item_name", ""),
            "category": request.form.get("category", ""),
            "description": request.form.get("description", ""),
            "quantity": request.form.get("quantity", "0"),
            "unit": request.form.get("unit", ""),
            "unit_price": request.form.get("unit_price", "0"),
            "supplier": request.form.get("supplier", ""),
            "reorder_level": request.form.get("reorder_level", "0"),
            "expiry_date": request.form.get("expiry_date", ""),
            "batch_number": request.form.get("batch_number", ""),
            "location": request.form.get("location", ""),
            "status": request.form.get("status", "In-Stock"),
        }
        HOGC.crud.record.update_record(UpdateRecordRequest(
            context=_ctx(), module_id=seed.INVENTORY_MODULE_ID, record_id=record_id, data=data
        ))
        flash("Inventory item updated successfully!", "success")
        return redirect(url_for("modules.inventory_detail", record_id=record_id))

    return render_template("modules/inventory/form.html", item=resp.data, action="edit")


@modules_bp.route("/inventory/<record_id>/delete", methods=["POST"])
@login_required
def inventory_delete(record_id):
    HOGC.crud.record.delete_record(DeleteRecordRequest(
        context=_ctx(), module_id=seed.INVENTORY_MODULE_ID, record_id=record_id
    ))
    flash("Inventory item deleted.", "success")
    return redirect(url_for("modules.inventory_list"))

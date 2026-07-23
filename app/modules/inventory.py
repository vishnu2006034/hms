import typing
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_required

from app.auth.utils import MODULE_CREATE, MODULE_EDIT, MODULE_DELETE, role_required
from app.services.inventory_service import InventoryService

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("/")
@login_required
def inventory_list() -> typing.Any:
    """Render paginated list of inventory items."""
    page: int = request.args.get("page", 1, type=int)
    search: str = request.args.get("search", "")

    result: dict[str, typing.Any] | None = InventoryService.list_items(search=search, page=page, page_size=20)
    if result is None:
        abort(403)

    return render_template(
        "modules/inventory/list.html",
        items=result["items"],
        page=result["page"],
        total_pages=result["total_pages"],
        total=result["total"],
        search=result["search"]
    )


@inventory_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_CREATE["inventory"])
def inventory_create() -> typing.Any:
    """Handle inventory item creation."""
    if request.method == "POST":
        InventoryService.create_item(request.form)
        flash("Inventory item created successfully!", "success")
        return redirect(url_for("inventory.inventory_list"))

    return render_template(
        "modules/inventory/form.html",
        item=None,
        action="create",
        picklists=InventoryService.get_picklists()
    )


@inventory_bp.route("/<record_id>")
@login_required
def inventory_detail(record_id: str) -> typing.Any:
    """View inventory item details."""
    detail: dict[str, typing.Any] | None = InventoryService.get_item_detail(record_id)
    if detail is None:
        flash("Item not found.", "danger")
        return redirect(url_for("inventory.inventory_list"))

    return render_template("modules/inventory/detail.html", item=detail["item"])


@inventory_bp.route("/<record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*MODULE_EDIT["inventory"])
def inventory_edit(record_id: str) -> typing.Any:
    """Handle inventory item editing."""
    detail: dict[str, typing.Any] | None = InventoryService.get_item_detail(record_id)
    if detail is None:
        flash("Item not found.", "danger")
        return redirect(url_for("inventory.inventory_list"))

    if request.method == "POST":
        InventoryService.update_item(record_id, request.form)
        flash("Inventory item updated successfully!", "success")
        return redirect(url_for("inventory.inventory_detail", record_id=record_id))

    return render_template(
        "modules/inventory/form.html",
        item=detail["item"],
        action="edit",
        picklists=InventoryService.get_picklists()
    )


@inventory_bp.route("/<record_id>/delete", methods=["POST"])
@login_required
@role_required(*MODULE_DELETE["inventory"])
def inventory_delete(record_id: str) -> typing.Any:
    """Handle inventory item deletion."""
    InventoryService.delete_item(record_id)
    flash("Inventory item deleted.", "success")
    return redirect(url_for("inventory.inventory_list"))

import typing
from app.config import Config
from app.seed import schema
from app.services.visibility_service import VisibilityService
from app.modules.routes_base import _ctx, _get_record, _get_picklist_options

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class InventoryService:
    """Business service layer for Hospital Inventory Item management using HOGC facade."""

    @staticmethod
    def get_picklists() -> dict[str, list[tuple[str, str]]]:
        """Fetch live picklist options for inventory forms."""
        return _get_picklist_options(schema.INVENTORY_MODULE_ID, "category", "status", "unit")

    @classmethod
    def list_items(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any] | None:
        """Fetch paginated inventory items list."""
        result = VisibilityService.get_inventory_items(search=search, page=page, page_size=page_size)
        if result is None:
            return None

        items = result.items
        total = result.total
        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
        }

    @classmethod
    def get_item_detail(cls, record_id: str) -> dict[str, typing.Any] | None:
        """Fetch details of a single inventory item."""
        resp = _get_record(schema.INVENTORY_MODULE_ID, record_id)
        if not resp.data:
            return None
        return {"item": resp.data}

    @classmethod
    def create_item(cls, form_data: dict[str, typing.Any]) -> typing.Any:
        """Create a new inventory item using HOGC facade."""
        data: dict[str, str] = {
            "item_name": form_data.get("item_name", ""),
            "category": form_data.get("category", ""),
            "description": form_data.get("description", ""),
            "quantity": form_data.get("quantity", "0"),
            "unit": form_data.get("unit", ""),
            "unit_price": form_data.get("unit_price", "0"),
            "supplier": form_data.get("supplier", ""),
            "reorder_level": form_data.get("reorder_level", "0"),
            "expiry_date": form_data.get("expiry_date", ""),
            "batch_number": form_data.get("batch_number", ""),
            "location": form_data.get("location", ""),
            "status": form_data.get("status", "In-Stock"),
        }
        req = CreateRecordRequest(context=_ctx(), module_id=schema.INVENTORY_MODULE_ID, data=data)
        return HOGC.crud.record.create(req)

    @classmethod
    def update_item(cls, record_id: str, form_data: dict[str, typing.Any]) -> dict[str, typing.Any] | None:
        """Update an existing inventory item using HOGC facade."""
        resp = _get_record(schema.INVENTORY_MODULE_ID, record_id)
        if not resp.data:
            return None

        data: dict[str, str] = {
            "item_name": form_data.get("item_name", ""),
            "category": form_data.get("category", ""),
            "description": form_data.get("description", ""),
            "quantity": form_data.get("quantity", "0"),
            "unit": form_data.get("unit", ""),
            "unit_price": form_data.get("unit_price", "0"),
            "supplier": form_data.get("supplier", ""),
            "reorder_level": form_data.get("reorder_level", "0"),
            "expiry_date": form_data.get("expiry_date", ""),
            "batch_number": form_data.get("batch_number", ""),
            "location": form_data.get("location", ""),
            "status": form_data.get("status", "In-Stock"),
        }
        req = UpdateRecordRequest(context=_ctx(), module_id=schema.INVENTORY_MODULE_ID, record_id=record_id, data=data)
        updated = HOGC.crud.record.update(req)
        return {"updated": updated}

    @classmethod
    def delete_item(cls, record_id: str) -> dict[str, typing.Any]:
        """Delete an inventory item using HOGC facade."""
        req = DeleteRecordRequest(context=_ctx(), module_id=schema.INVENTORY_MODULE_ID, record_id=record_id)
        HOGC.crud.record.delete(req)
        return {"success": True}

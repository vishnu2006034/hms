from flask import Blueprint, jsonify
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListLayoutsRequest
from app.modules.routes_base import _ctx


layout_api_bp = Blueprint("layout_api", __name__, url_prefix="/api/layouts")

@layout_api_bp.route("/<module_id>")
def get_layouts(module_id: str):
    """Get the layouts for a specific module."""
    try:
        layouts_resp = HOGC.crud.layout.list(ListLayoutsRequest(context=_ctx(), module_id=module_id))
        
        items = []
        if layouts_resp and hasattr(layouts_resp, 'items'):
            for layout in layouts_resp.items:
                if hasattr(layout, 'model_dump'):
                    items.append(layout.model_dump())
                elif hasattr(layout, 'dict'):
                    items.append(layout.dict())
                else:
                    items.append(layout)
                    
        return jsonify({
            "status": "success",
            "data": items
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

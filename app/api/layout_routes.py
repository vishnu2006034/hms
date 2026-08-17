import typing
from flask import Blueprint, jsonify
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListLayoutsRequest
from app.modules.routes_base import _ctx


layout_api_bp = Blueprint("layout_api", __name__, url_prefix="/api/layouts")

@layout_api_bp.route("/<module_id>")
def get_layouts(module_id: str) -> typing.Any:
    """Return a JSON list of layouts for the requested module.

    Args:
        module_id: The HOGC module UUID from the URL path.

    Returns:
        A JSON response with ``status='success'`` and ``data`` containing a
        list of serialised layout dicts, or a ``status='error'`` response
        with HTTP 500 on failure.
    """
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

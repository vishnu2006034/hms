import typing
from app.modules.routes_base import _ctx
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListLayoutsRequest, GetLayoutRequest

class LayoutServiceImpl:
    """Service to handle layout operations using the HOGC CRUD engine."""

    @classmethod
    def get_layouts_for_module(cls, module_id: str) -> typing.Any:
        """Fetch layouts for a given module from the HOGC CRUD engine."""
        req = ListLayoutsRequest(context=_ctx(), module_id=module_id)
        # Calling the list method defined in LayoutAPI
        resp = HOGC.crud.layout.list(req)
        return resp

    @classmethod
    def get_layout(cls, layout_id: str) -> typing.Any:
        """Fetch a specific layout by ID."""
        req = GetLayoutRequest(context=_ctx(), layout_id=layout_id)
        resp = HOGC.crud.layout.get(req)
        return resp

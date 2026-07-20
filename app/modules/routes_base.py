import typing
from flask_login import login_required, current_user

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest, ListModulesRequest, GetRecordRequest, DeleteRecordRequest
)

from app.config import Config


def _ctx() -> RequestContext:
    """Get the RequestContext for the current user."""
    user_id: str = str(current_user.id) if current_user.is_authenticated else "system"
    roles: list[str] = [current_user.role] if current_user.is_authenticated else []
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=user_id,
        roles=roles,
    )


def _get_record_display_name(module_id: str, record_id: str) -> str:
    """Get a human-readable display name for a record (first text field found)."""
    if not record_id:
        return "-"
    ctx: RequestContext = _ctx()
    try:
        resp = HOGC.crud.record.get(GetRecordRequest(context=ctx, module_id=module_id, record_id=record_id))
        if resp and resp.data:
            d: dict = resp.data.data
            for key in ("full_name", "first_name", "item_name", "test_name", "medication_name", "name"):
                val = d.get(key)
                if val:
                    if key == "first_name":
                        last_name: str = d.get('last_name', '')
                        return f"{val} {last_name}"
                    return val
            for k, v in d.items():
                if v and isinstance(v, str) and len(v) < 100:
                    return v
        return record_id[:8]
    except Exception:
        return record_id[:8]


def _resolve_lookups(records: list, *field_module_pairs: str) -> dict:
    """Resolve lookup fields to display names.
    
    Args:
        records: list of record objects with .data dicts
        field_module_pairs: alternating field_name, module_id pairs
            e.g. 'patient_lookup', PATIENTS_MODULE_ID, 'doctor_lookup', USERS_MODULE_ID
    
    Returns:
        dict of {record_id: {field_name: display_name, ...}}
    """
    field_names: tuple = field_module_pairs[::2]
    module_ids: tuple = field_module_pairs[1::2]
    lookup_map: dict = {}
    for i, field_name in enumerate(field_names):
        mod_id: str = module_ids[i]
        ids: set = set()
        for r in records:
            val = r.data.get(field_name)
            if val:
                ids.add(val)
        lookup_map[field_name] = {}
        for rid in ids:
            lookup_map[field_name][rid] = _get_record_display_name(mod_id, rid)
    
    result: dict = {}
    for r in records:
        resolved: dict = {}
        for field_name in field_names:
            raw = r.data.get(field_name)
            resolved[field_name] = lookup_map[field_name].get(raw, raw or "-")
        result[r.id] = resolved
    return result


def _get_records(module_id: str, page: int = 1, page_size: int = 20, search: typing.Optional[str] = None, search_field: typing.Optional[str] = None, extra_filters: typing.Optional[list] = None) -> typing.Any:
    """Fetch paginated records with optional filters."""
    ctx: RequestContext = _ctx()
    filters: list = extra_filters or []
    if search and search_field:
        filters.append(QueryFilter(field=search_field, operator="contains", value=search))
    
    if filters:
        query: RecordQuery = RecordQuery(
            module_id=module_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )
        return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
    
    return HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=module_id, page=page, page_size=page_size
    ))


def _get_all_records(module_id: str, page_size: int = 200) -> list:
    """Fetch all records from a module (for dropdown population)."""
    ctx: RequestContext = _ctx()
    return HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=module_id, page=1, page_size=page_size
    )).items


class _GetReq:
    """Internal request wrapper."""
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_record(module_id: str, record_id: str) -> typing.Any:
    """Get a single record by ID."""
    return HOGC.crud.record.get(
        _GetReq(context=_ctx(), module_id=module_id, record_id=record_id)
    )


def _create_record(module_id: str, data: dict) -> typing.Any:
    """Create a new record."""
    return HOGC.crud.record.create(CreateRecordRequest(
        context=_ctx(), module_id=module_id, data=data
    ))


def _update_record(module_id: str, record_id: str, data: dict) -> typing.Any:
    """Update an existing record."""
    return HOGC.crud.record.update(UpdateRecordRequest(
        context=_ctx(), module_id=module_id, record_id=record_id, data=data
    ))


def _delete_record(module_id: str, record_id: str) -> typing.Any:
    """Delete a record."""
    return HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=module_id, record_id=record_id
    ))


def _check_access(record: typing.Any, lookup_field: str) -> bool:
    """
    Checks if the current user (if a Doctor) is authorized to access the record.
    Returns True if access is allowed, False otherwise.
    """
    if current_user.role == "Doctor":
        assigned_id: str = record.data.get(lookup_field)
        if assigned_id != current_user.hogc_record_id:
            return False
    return True

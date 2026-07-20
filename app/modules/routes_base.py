from hogc.lib import HOGC
from flask_login import login_required, current_user

from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest, ListModulesRequest, GetRecordRequest,
)
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter


def _ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=str(current_user.id) if current_user.is_authenticated else "system",
        roles=[current_user.role] if current_user.is_authenticated else [],
    )


def _get_record_display_name(module_id, record_id):
    """Get a human-readable display name for a record (first text field found)."""
    if not record_id:
        return "-"
    ctx = _ctx()
    try:
        resp = HOGC.crud.record.get(GetRecordRequest(context=ctx, module_id=module_id, record_id=record_id))
        if resp and resp.data:
            d = resp.data.data
            for key in ("full_name", "first_name", "item_name", "test_name", "medication_name", "name"):
                val = d.get(key)
                if val:
                    if key == "first_name":
                        return f"{val} {d.get('last_name', '')}"
                    return val
            for k, v in d.items():
                if v and isinstance(v, str) and len(v) < 100:
                    return v
        return record_id[:8]
    except Exception:
        return record_id[:8]


def _resolve_lookups(records, *field_module_pairs):
    """Resolve lookup fields to display names.
    
    Args:
        records: list of record objects with .data dicts
        field_module_pairs: alternating field_name, module_id pairs
            e.g. 'patient_lookup', PATIENTS_MODULE_ID, 'doctor_lookup', USERS_MODULE_ID
    
    Returns:
        dict of {record_id: {field_name: display_name, ...}}
    """
    field_names = field_module_pairs[::2]
    module_ids = field_module_pairs[1::2]
    lookup_map = {}
    for i, field_name in enumerate(field_names):
        mod_id = module_ids[i]
        ids = set()
        for r in records:
            val = r.data.get(field_name)
            if val:
                ids.add(val)
        lookup_map[field_name] = {
            rid: _get_record_display_name(mod_id, rid)
            for rid in ids
        }
    result = {}
    for r in records:
        resolved = {}
        for field_name in field_names:
            raw = r.data.get(field_name)
            resolved[field_name] = lookup_map[field_name].get(raw, raw or "-")
        result[r.id] = resolved
    return result


def _get_records(module_id, page=1, page_size=20, search=None, search_field=None):
    ctx = _ctx()
    if search and search_field:
        query = RecordQuery(
            module_id=module_id,
            filters=[QueryFilter(field=search_field, operator="contains", value=search)],
            page=page,
            page_size=page_size,
        )
        return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
    return HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=module_id, page=page, page_size=page_size
    ))


def _get_all_records(module_id, page_size=200):
    """Fetch all records from a module (for dropdown population)."""
    ctx = _ctx()
    return HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=module_id, page=1, page_size=page_size
    )).items


class _GetReq:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _get_record(module_id, record_id):
    return HOGC.crud.record.get(
        _GetReq(context=_ctx(), module_id=module_id, record_id=record_id)
    )


def _create_record(module_id, data):
    return HOGC.crud.record.create(CreateRecordRequest(
        context=_ctx(), module_id=module_id, data=data
    ))


def _update_record(module_id, record_id, data):
    return HOGC.crud.record.update(UpdateRecordRequest(
        context=_ctx(), module_id=module_id, record_id=record_id, data=data
    ))


def _delete_record(module_id, record_id):
    from hogc.lib.contracts.crud.requests import DeleteRecordRequest
    return HOGC.crud.record.delete(DeleteRecordRequest(
        context=_ctx(), module_id=module_id, record_id=record_id
    ))

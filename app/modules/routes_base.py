import typing
from flask_login import login_required, current_user

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest, ListModulesRequest, GetRecordRequest, DeleteRecordRequest,
    LinkRecordsRequest, UnlinkRecordsRequest, GetRelatedRecordsRequest, ListRelationshipsForRecordRequest,
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


# ── Relationship helpers ──────────────────────────────────────────────

def _link_related_records(ctx: RequestContext, relationship_id: str, from_record_id: str, to_record_id: str, attributes: typing.Optional[dict] = None) -> typing.Any:
    """Create a link between two records via a relationship definition."""
    return HOGC.crud.related_records.link(LinkRecordsRequest(
        context=ctx,
        relationship_id=relationship_id,
        from_record_id=from_record_id,
        to_record_id=to_record_id,
        attributes=attributes or {},
    ))


def _unlink_related_records(ctx: RequestContext, relationship_id: str, from_record_id: str, to_record_id: str) -> typing.Any:
    """Remove a link between two records."""
    return HOGC.crud.related_records.unlink(UnlinkRecordsRequest(
        context=ctx,
        relationship_id=relationship_id,
        from_record_id=from_record_id,
        to_record_id=to_record_id,
    ))


def _get_related_records(ctx: RequestContext, relationship_id: str, record_id: str, page: int = 1, page_size: int = 50) -> typing.Any:
    """Get records related to a specific record within a relationship."""
    return HOGC.crud.related_records.get_related(GetRelatedRecordsRequest(
        context=ctx,
        relationship_id=relationship_id,
        record_id=record_id,
        page=page,
        page_size=page_size,
    ))


def _list_record_relationships(ctx: RequestContext, module_id: str, record_id: str) -> typing.Any:
    """List all relationships involving a record."""
    return HOGC.crud.related_records.list_relationships(ListRelationshipsForRecordRequest(
        context=ctx,
        module_id=module_id,
        record_id=record_id,
    ))


def _sync_related_record_on_create(ctx: RequestContext, module_id: str, record_id: str, data: dict) -> None:
    """After creating a record with LOOKUP fields, also create related_record links.

    Works for: Visits, Prescriptions, Laboratory.
    """
    from app.seed import schema as s
    patient_id = data.get("patient_lookup", "")
    doctor_id = data.get("doctor_lookup", "")
    visit_id = data.get("visit_lookup", "")

    if module_id == s.VISITS_MODULE_ID:
        if patient_id and s.PATIENTS_VISITS_REL_ID:
            _link_related_records(ctx, s.PATIENTS_VISITS_REL_ID, patient_id, record_id)
        if doctor_id and s.USERS_VISITS_REL_ID:
            _link_related_records(ctx, s.USERS_VISITS_REL_ID, doctor_id, record_id)

    elif module_id == s.PRESCRIPTIONS_MODULE_ID:
        if patient_id and s.PATIENTS_PRESCRIPTIONS_REL_ID:
            _link_related_records(ctx, s.PATIENTS_PRESCRIPTIONS_REL_ID, patient_id, record_id)
        if visit_id and s.VISITS_PRESCRIPTIONS_REL_ID:
            _link_related_records(ctx, s.VISITS_PRESCRIPTIONS_REL_ID, visit_id, record_id)

    elif module_id == s.LABORATORY_MODULE_ID:
        if patient_id and s.PATIENTS_LABORATORY_REL_ID:
            _link_related_records(ctx, s.PATIENTS_LABORATORY_REL_ID, patient_id, record_id)
        if visit_id and s.VISITS_LABORATORY_REL_ID:
            _link_related_records(ctx, s.VISITS_LABORATORY_REL_ID, visit_id, record_id)


def _sync_related_record_on_update(ctx: RequestContext, module_id: str, record_id: str, old_data: dict, new_data: dict) -> None:
    """Update related_record links when a record's LOOKUP fields change."""
    from app.seed import schema as s
    _sync_related_record_on_delete(ctx, module_id, record_id, old_data)
    _sync_related_record_on_create(ctx, module_id, record_id, new_data)


def _sync_related_record_on_delete(ctx: RequestContext, module_id: str, record_id: str, old_data: typing.Optional[dict] = None) -> None:
    """Remove all related_record links when a record is deleted."""
    from app.seed import schema as s
    _unlink_relation(ctx, old_data, record_id, s.PATIENTS_VISITS_REL_ID, module_id, s.PATIENTS_MODULE_ID, "patient_lookup")
    _unlink_relation(ctx, old_data, record_id, s.USERS_VISITS_REL_ID, module_id, s.USERS_MODULE_ID, "doctor_lookup")
    _unlink_relation(ctx, old_data, record_id, s.PATIENTS_PRESCRIPTIONS_REL_ID, module_id, s.PATIENTS_MODULE_ID, "patient_lookup")
    _unlink_relation(ctx, old_data, record_id, s.VISITS_PRESCRIPTIONS_REL_ID, module_id, s.VISITS_MODULE_ID, "visit_lookup")
    _unlink_relation(ctx, old_data, record_id, s.PATIENTS_LABORATORY_REL_ID, module_id, s.PATIENTS_MODULE_ID, "patient_lookup")
    _unlink_relation(ctx, old_data, record_id, s.VISITS_LABORATORY_REL_ID, module_id, s.VISITS_MODULE_ID, "visit_lookup")


def _unlink_relation(ctx: RequestContext, old_data: typing.Optional[dict], record_id: str, rel_id: typing.Optional[str],
                     module_id: str, from_module_id: str, lookup_field: str) -> None:
    """Unlink records for a given relationship (handles both directions)."""
    if not rel_id:
        return
    if module_id == from_module_id:
        fp = _get_related_records(ctx, rel_id, record_id, page_size=200)
        if fp and fp.items:
            for link in fp.items:
                try:
                    _unlink_related_records(ctx, rel_id, link.from_record_id, link.to_record_id)
                except Exception:
                    pass
    elif old_data:
        from_id = old_data.get(lookup_field, "")
        if from_id:
            try:
                _unlink_related_records(ctx, rel_id, from_id, record_id)
            except Exception:
                pass



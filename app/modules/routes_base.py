from hogc.lib import HOGC
from flask_login import login_required, current_user

from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest,
)
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter


def _ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=str(current_user.id) if current_user.is_authenticated else "system",
        roles=[current_user.role] if current_user.is_authenticated else [],
    )


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

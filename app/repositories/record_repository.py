from flask_login import current_user
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest, GetRecordRequest, DeleteRecordRequest
)
from hogc.lib.contracts.crud.models import RecordQuery
from hogc.lib import HOGC


class _GetReq:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RecordRepository:
    """Repository for managing HOGC records with RequestContext."""

    @staticmethod
    def _ctx():
        return RequestContext(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            user_id=str(current_user.id) if current_user.is_authenticated else "system",
            roles=[current_user.role] if current_user.is_authenticated else [],
        )

    @classmethod
    def get_records(cls, module_id, page=1, page_size=20, filters=None):
        ctx = cls._ctx()
        if filters:
            query = RecordQuery(
                module_id=module_id,
                filters=filters,
                page=page,
                page_size=page_size,
            )
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query))
        
        return HOGC.crud.record.list(ListRecordsRequest(
            context=ctx, module_id=module_id, page=page, page_size=page_size
        ))

    @classmethod
    def get_all_records(cls, module_id, page_size=200, filters=None):
        ctx = cls._ctx()
        if filters:
            query = RecordQuery(
                module_id=module_id,
                filters=filters,
                page=1,
                page_size=page_size,
            )
            return HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=query)).items

        return HOGC.crud.record.list(ListRecordsRequest(
            context=ctx, module_id=module_id, page=1, page_size=page_size
        )).items

    @classmethod
    def get_record(cls, module_id, record_id):
        return HOGC.crud.record.get(
            _GetReq(context=cls._ctx(), module_id=module_id, record_id=record_id)
        )

    @classmethod
    def create_record(cls, module_id, data):
        return HOGC.crud.record.create(CreateRecordRequest(
            context=cls._ctx(), module_id=module_id, data=data
        ))

    @classmethod
    def update_record(cls, module_id, record_id, data):
        return HOGC.crud.record.update(UpdateRecordRequest(
            context=cls._ctx(), module_id=module_id, record_id=record_id, data=data
        ))

    @classmethod
    def delete_record(cls, module_id, record_id):
        return HOGC.crud.record.delete(DeleteRecordRequest(
            context=cls._ctx(), module_id=module_id, record_id=record_id
        ))

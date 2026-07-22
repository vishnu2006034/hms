import typing
from flask_login import current_user

from app.config import Config

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.models import RecordQuery, QueryFilter
from hogc.lib.contracts.crud.requests import (
    CreateRecordRequest, UpdateRecordRequest, ListRecordsRequest, QueryRecordsRequest, GetRecordRequest, DeleteRecordRequest
)


class RecordRepository:
    """Repository for managing HOGC records with RequestContext."""

    @staticmethod
    def _ctx() -> RequestContext:
        """Create and return RequestContext for the current user."""
        user_id: str = "system"
        roles: list[str] = []
        try:
            if current_user and current_user.is_authenticated:
                user_id = str(current_user.id)
                roles = [current_user.role]
        except Exception:
            pass
        return RequestContext(
            tenant_id=Config.HOGC_TENANT_ID,
            org_id=Config.HOGC_ORG_ID,
            user_id=user_id,
            roles=roles,
        )

    @classmethod
    def get_records(
        cls, 
        module_id: str, 
        page: int = 1, 
        page_size: int = 20, 
        filters: typing.Optional[list[QueryFilter]] = None
    ) -> typing.Any:
        """Fetch paginated records with optional filters."""
        ctx: RequestContext = cls._ctx()
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

    @classmethod
    def get_all_records(
        cls, 
        module_id: str, 
        page_size: int = 200, 
        filters: typing.Optional[list[QueryFilter]] = None
    ) -> list[typing.Any]:
        """Fetch all records up to page_size, with optional filters."""
        ctx: RequestContext = cls._ctx()
        if filters:
            query: RecordQuery = RecordQuery(
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
    def get_record(cls, module_id: str, record_id: str) -> typing.Any:
        """Fetch a specific record by ID."""
        req = GetRecordRequest(context=cls._ctx(), module_id=module_id, record_id=record_id)
        return HOGC.crud.record.get(req)

    @classmethod
    def create_record(cls, module_id: str, data: dict[str, typing.Any]) -> typing.Any:
        """Create a new record in the given module."""
        req = CreateRecordRequest(context=cls._ctx(), module_id=module_id, data=data)
        return HOGC.crud.record.create(req)

    @classmethod
    def update_record(cls, module_id: str, record_id: str, data: dict[str, typing.Any]) -> typing.Any:
        """Update an existing record."""
        req = UpdateRecordRequest(context=cls._ctx(), module_id=module_id, record_id=record_id, data=data)
        return HOGC.crud.record.update(req)

    @classmethod
    def delete_record(cls, module_id: str, record_id: str) -> typing.Any:
        """Delete an existing record."""
        req = DeleteRecordRequest(context=cls._ctx(), module_id=module_id, record_id=record_id)
        return HOGC.crud.record.delete(req)

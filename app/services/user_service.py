import typing
from app.config import Config
from app.seed import schema
from app.extensions import db
from app.auth.models import AuthUser
from app.modules.routes_base import _ctx, _get_records, _get_record, _sync_related_record_on_delete

from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import CreateRecordRequest, UpdateRecordRequest, DeleteRecordRequest


class UserService:
    """Business service layer for Hospital Staff / Users management using HOGC facade."""

    @classmethod
    def list_users(cls, search: str = "", page: int = 1, page_size: int = 20) -> dict[str, typing.Any]:
        """Fetch paginated staff/user records from HOGC facade."""
        result = _get_records(
            schema.USERS_MODULE_ID,
            page=page,
            page_size=page_size,
            search=search,
            search_field="full_name"
        )
        users = result.items
        total = result.total
        total_pages = (total + page_size - 1) // page_size

        return {
            "users": users,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "search": search,
        }

    @classmethod
    def get_user_detail(cls, record_id: str) -> dict[str, typing.Any] | None:
        """Fetch user record by ID."""
        resp = _get_record(schema.USERS_MODULE_ID, record_id)
        if not resp.data:
            return None
        return {"user": resp.data}

    @classmethod
    def create_user(cls, form_data: dict[str, typing.Any]) -> typing.Any:
        """Create a new staff user in AuthUser and sync HOGC record using HOGC facade."""
        username = form_data.get("username", "")
        email = form_data.get("email", "")
        full_name = form_data.get("full_name", "")
        role = form_data.get("role", "Doctor")
        password = form_data.get("password", "password123")

        auth_user = AuthUser(username=username, email=email, full_name=full_name, role=role)
        auth_user.set_password(password)
        db.session.add(auth_user)
        db.session.commit()

        data: dict[str, str] = {
            "full_name": full_name,
            "email": email,
            "phone": form_data.get("phone", ""),
            "role": role,
            "department": form_data.get("department", ""),
            "is_active": "true",
        }
        resp = HOGC.crud.record.create(CreateRecordRequest(
            context=_ctx(), module_id=schema.USERS_MODULE_ID, data=data
        ))
        auth_user.hogc_record_id = resp.data.id
        db.session.commit()
        return {"auth_user": auth_user, "record": resp.data}

    @classmethod
    def update_user(cls, record_id: str, form_data: dict[str, typing.Any]) -> dict[str, typing.Any] | None:
        """Update staff user record using HOGC facade."""
        resp = _get_record(schema.USERS_MODULE_ID, record_id)
        if not resp.data:
            return None

        data: dict[str, str] = {
            "full_name": form_data.get("full_name", ""),
            "email": form_data.get("email", ""),
            "phone": form_data.get("phone", ""),
            "role": form_data.get("role", ""),
            "department": form_data.get("department", ""),
            "is_active": form_data.get("is_active", "true"),
        }
        updated = HOGC.crud.record.update(UpdateRecordRequest(
            context=_ctx(), module_id=schema.USERS_MODULE_ID, record_id=record_id, data=data
        ))
        return {"updated": updated}

    @classmethod
    def delete_user(cls, record_id: str) -> dict[str, typing.Any]:
        """Delete staff user record using HOGC facade and cleanup relations."""
        ctx = _ctx()
        _sync_related_record_on_delete(ctx, schema.USERS_MODULE_ID, record_id)
        HOGC.crud.record.delete(DeleteRecordRequest(
            context=ctx, module_id=schema.USERS_MODULE_ID, record_id=record_id
        ))
        return {"success": True}

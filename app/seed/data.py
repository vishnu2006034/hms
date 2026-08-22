"""Seed data - Default admin user."""
import typing

from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import CreateRecordRequest

from app.config import Config
from app.extensions import db


def _ctx() -> RequestContext:
    """Build a system-level RequestContext for seed data operations.

    Returns:
        A RequestContext populated with tenant/org from Config and the 'Admin' role.
    """
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )


def _create_default_admin(module_id: str) -> None:
    """Ensure a default admin AuthUser and matching HOGC record exist.

    Creates both the SQLAlchemy AuthUser row and the corresponding HOGC
    record in the users module only when no admin user exists yet.
    Silently ignores failures when creating the HOGC record.

    Args:
        module_id: UUID of the 'users' HOGC module, used when creating the
                   corresponding HOGC record for the admin user.
    """
    from app.auth.models import AuthUser
    admin: typing.Optional[AuthUser] = AuthUser.query.filter_by(username="admin").first()
    if admin is None:
        admin = AuthUser(
            username="admin",
            email="admin@hospital.com",
            full_name="System Admin",
            role="Admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        try:
            ctx: RequestContext = _ctx()
            record = HOGC.crud.record.create(CreateRecordRequest(
                context=ctx,
                module_id=module_id,
                data={
                    "full_name": "System Admin",
                    "email": "admin@hospital.com",
                    "role": "Admin",
                    "is_active": "true",
                },
            ))
            admin.hogc_record_id = record.data.id
            db.session.commit()
        except Exception:
            pass
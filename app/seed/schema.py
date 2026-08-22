"""Seed schema — Module, field, picklist, and relationship creation helpers."""
import typing
from hogc.lib import HOGC
import uuid
from app import extensions
from app.extensions import db
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import (
    CreateModuleRequest, CreateFieldRequest, AddPicklistOptionRequest,
    ListModulesRequest, CreateLayoutRequest,
)
from hogc.lib.contracts.crud.types import FieldType
from hogc.engines.crud.schema import RelationshipDefinition


# Module IDs - set after creation
USERS_MODULE_ID = None
PATIENTS_MODULE_ID = None
VISITS_MODULE_ID = None
INVENTORY_MODULE_ID = None
PRESCRIPTIONS_MODULE_ID = None
LABORATORY_MODULE_ID = None

# Relationship definition IDs - set after creation
PATIENTS_VISITS_REL_ID = None
VISITS_PRESCRIPTIONS_REL_ID = None
VISITS_LABORATORY_REL_ID = None
PATIENTS_PRESCRIPTIONS_REL_ID = None
PATIENTS_LABORATORY_REL_ID = None
USERS_VISITS_REL_ID = None
PATIENTS_DOCTORS_REL_ID = None


def _ctx() -> RequestContext:
    """Build a system-level RequestContext for seeding operations.

    Returns:
        A RequestContext with tenant/org from Config and the 'Admin' role.
    """
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id="system",
        roles=["Admin"],
    )






def _drop_all_hogc() -> None:
    """Delete all HOGC records for the configured tenant, then truncate auth_users.

    Executes DELETE statements for every HOGC table in dependency order so
    that foreign-key constraints are satisfied.  Rolls back automatically on
    any exception and always closes the session.
    """
    session = extensions.SessionLocal()
    try:
        for table in ["related_records", "relationship_definitions",
                      "picklist_options", "records", "layouts", "fields", "modules"]:
            session.execute(db.text(f"DELETE FROM {table} WHERE tenant_id = :tid"), {"tid": Config.HOGC_TENANT_ID})
        session.execute(db.text("DELETE FROM auth_users"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _lookup_module_ids() -> None:
    """Populate the module ID globals by querying existing HOGC modules.

    Reads all modules for the configured tenant and sets each of the six
    module-level ID globals (USERS_MODULE_ID, PATIENTS_MODULE_ID, etc.).
    Calls _lookup_relationship_ids() once all IDs are resolved.
    """
    global USERS_MODULE_ID, PATIENTS_MODULE_ID, VISITS_MODULE_ID
    global INVENTORY_MODULE_ID, PRESCRIPTIONS_MODULE_ID, LABORATORY_MODULE_ID
    existing = HOGC.crud.module.list(ListModulesRequest(
        context=_ctx(), page=1, page_size=50
    ))
    for m in existing.items:
        if m.api_name == "users":
            USERS_MODULE_ID = m.id
        elif m.api_name == "patients":
            PATIENTS_MODULE_ID = m.id
        elif m.api_name == "visits":
            VISITS_MODULE_ID = m.id
        elif m.api_name == "inventory":
            INVENTORY_MODULE_ID = m.id
        elif m.api_name == "prescriptions":
            PRESCRIPTIONS_MODULE_ID = m.id
        elif m.api_name == "laboratory":
            LABORATORY_MODULE_ID = m.id
    _lookup_relationship_ids()


def _lookup_relationship_ids() -> None:
    """Populate relationship ID globals by querying relationship_definitions directly.

    Runs a raw SQL SELECT against the relationship_definitions table to find
    the UUIDs of the six predefined inter-module relationships and assigns
    each to its corresponding module-level global constant.
    """
    global PATIENTS_VISITS_REL_ID, VISITS_PRESCRIPTIONS_REL_ID, VISITS_LABORATORY_REL_ID
    global PATIENTS_PRESCRIPTIONS_REL_ID, PATIENTS_LABORATORY_REL_ID, USERS_VISITS_REL_ID
    global PATIENTS_DOCTORS_REL_ID
    session = extensions.SessionLocal()
    try:
        rows = session.execute(db.text("""
            SELECT id, from_module_id, to_module_id, relationship_type, from_field_name
            FROM relationship_definitions
            WHERE tenant_id = :tid AND org_id = :oid AND status = 'active'
        """), {"tid": Config.HOGC_TENANT_ID, "oid": Config.HOGC_ORG_ID}).fetchall()
        for row in rows:
            rid, from_mid, to_mid, rtype, from_field = row
            if from_mid == PATIENTS_MODULE_ID and to_mid == VISITS_MODULE_ID:
                PATIENTS_VISITS_REL_ID = rid
            elif from_mid == VISITS_MODULE_ID and to_mid == PRESCRIPTIONS_MODULE_ID:
                VISITS_PRESCRIPTIONS_REL_ID = rid
            elif from_mid == VISITS_MODULE_ID and to_mid == LABORATORY_MODULE_ID:
                VISITS_LABORATORY_REL_ID = rid
            elif from_mid == PATIENTS_MODULE_ID and to_mid == PRESCRIPTIONS_MODULE_ID:
                PATIENTS_PRESCRIPTIONS_REL_ID = rid
            elif from_mid == PATIENTS_MODULE_ID and to_mid == LABORATORY_MODULE_ID:
                PATIENTS_LABORATORY_REL_ID = rid
            elif from_mid == USERS_MODULE_ID and to_mid == VISITS_MODULE_ID:
                USERS_VISITS_REL_ID = rid
            elif from_mid == PATIENTS_MODULE_ID and to_mid == USERS_MODULE_ID and rtype == "many_to_many":
                PATIENTS_DOCTORS_REL_ID = rid
    finally:
        session.close()

"""Seed orchestrator — creates schema and populates sample data."""
from pathlib import Path
import json
from sqlalchemy import text
from app import extensions
from app.extensions import db
from app.config import Config
from hogc.lib import HOGC
from hogc.lib.contracts.crud.requests import ListModulesRequest, GetModuleRequest
from app.seed.schema import (
    _ctx, _drop_all_hogc, _lookup_module_ids,
)
from app.seed.data import _create_default_admin


def seed_from_json(file_path: str) -> dict[str, int]:
    """Seed modules, fields, layouts, relationships, and records from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the definition.
        
    Returns:
        A dictionary with counts of created entities.
    """
    ctx = _ctx()
    
    # 1. Seed native CRUD engine schema (Modules, Fields, Layouts)
    summary = HOGC.crud.seed_crud(ctx, file_path)
    
    # Reload modules to get their IDs
    _lookup_module_ids()
    from app.seed import schema
    
    module_api_to_id = {
        "users": schema.USERS_MODULE_ID,
        "patients": schema.PATIENTS_MODULE_ID,
        "visits": schema.VISITS_MODULE_ID,
        "inventory": schema.INVENTORY_MODULE_ID,
        "prescriptions": schema.PRESCRIPTIONS_MODULE_ID,
        "laboratory": schema.LABORATORY_MODULE_ID
    }
    
    # 2. Parse relationships and records
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    session = extensions.SessionLocal()
    try:
        if "relationships" in data:
            import uuid
            for rel in data["relationships"]:
                from_mod = module_api_to_id.get(rel["from_module_api_name"])
                to_mod = module_api_to_id.get(rel["to_module_api_name"])
                if not from_mod or not to_mod:
                    continue
                session.execute(text("""
                    INSERT INTO relationship_definitions 
                    (id, tenant_id, org_id, from_module_id, to_module_id, relationship_type, from_field_name, to_field_name, status, cascade_delete, created_at, updated_at, created_by, updated_by, version, tags_json, metadata_json)
                    VALUES (:id, :tid, :oid, :fmid, :tmid, :rtype, :fname, :tname, 'active', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system', 'system', 1, '[]'::jsonb, '{}'::jsonb)
                """), {
                    "id": uuid.uuid4().hex,
                    "tid": Config.HOGC_TENANT_ID,
                    "oid": Config.HOGC_ORG_ID,
                    "fmid": from_mod,
                    "tmid": to_mod,
                    "rtype": rel["relationship_type"],
                    "fname": rel.get("from_field_name", ""),
                    "tname": rel.get("to_field_name", "")
                })
            session.commit()
            schema._lookup_relationship_ids()
            
        if "records" in data:
            # We must use HOGC's _seed_records or custom resolving to handle inter-record links.
            # Using _seed_records allows _ref: resolution across batches.
            record_defs = []
            for rec in data["records"]:
                api_name = rec["module_api_name"]
                mod_id = module_api_to_id.get(api_name)
                if not mod_id:
                    continue
                record_defs.append((mod_id, api_name, rec))
                
            seed_id_to_engine_id = {api: {} for api in module_api_to_id.keys()}
            HOGC.crud._svc._seed_records(ctx, record_defs, seed_id_to_engine_id)
            
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return summary


def _do_seed() -> None:
    """Run the full seed sequence using the JSON seed mechanism.
    """
    _drop_all_hogc()
    
    json_path = str(Path(__file__).parent / "seed.json")
    print("Executing JSON seed process...")
    seed_from_json(json_path)
    
    # Ensure default admin AuthUser is created
    from app.seed.schema import USERS_MODULE_ID
    if USERS_MODULE_ID:
        _create_default_admin(USERS_MODULE_ID)
    
    # Final lookup check
    _lookup_module_ids()
    print("Database seeding completed.")


def seed_modules(app: "Flask") -> None:
    """Ensure HOGC schema tables exist and seed default data if the database is empty.

    Runs inside an application context.  On a fresh database (no modules
    found) the full seed sequence is executed via _do_seed.  On an existing
    database, module IDs are looked up; if any module is missing its fields
    the database is wiped and re-seeded.

    Args:
        app: The Flask application instance used to push an application context.
    """
    with app.app_context():
        from hogc.engines.crud import Base as HogcBase
        HogcBase.metadata.create_all(db.engine)

        from app.auth.models import AuthUser
        db.create_all()

        existing = HOGC.crud.module.list(ListModulesRequest(
            context=_ctx(), page=1, page_size=50
        ))

        if existing.total == 0:
            _do_seed()
        else:
            _lookup_module_ids()
            has_fields = False
            for m in existing.items:
                try:
                    mod_resp = HOGC.crud.module.get(
                        GetModuleRequest(context=_ctx(), module_id=m.id)
                    )
                    if mod_resp.data and mod_resp.data.fields:
                        has_fields = True
                        break
                except Exception:
                    pass
            if not has_fields:
                _drop_all_hogc()
                try:
                    _do_seed()
                except Exception as e:
                    import sys
                    print(f"ERROR: Seed failed: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()

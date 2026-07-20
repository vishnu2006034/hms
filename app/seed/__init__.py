"""Seed orchestrator — creates schema and populates sample data."""
from hogc.lib import HOGC
from app.extensions import db
from hogc.lib.contracts.crud.requests import ListModulesRequest
from app.seed.schema import (
    _ctx, _GetReq, _seed_users_module, _seed_patients_module, _seed_visits_module,
    _seed_inventory_module, _seed_prescriptions_module, _seed_laboratory_module,
    _seed_relationships, _drop_all_hogc, _lookup_module_ids,
)
from app.seed.data import _create_default_admin, _seed_default_data


def _do_seed():
    from app.seed import schema
    _seed_users_module()
    _seed_patients_module()
    _seed_visits_module()
    _seed_inventory_module()
    _seed_prescriptions_module()
    _seed_laboratory_module()
    _seed_relationships()
    _create_default_admin(schema.USERS_MODULE_ID)
    _seed_default_data({
        "users": schema.USERS_MODULE_ID,
        "patients": schema.PATIENTS_MODULE_ID,
        "visits": schema.VISITS_MODULE_ID,
        "inventory": schema.INVENTORY_MODULE_ID,
        "prescriptions": schema.PRESCRIPTIONS_MODULE_ID,
        "laboratory": schema.LABORATORY_MODULE_ID,
    })


def seed_modules(app):
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
                        _GetReq(context=_ctx(), module_id=m.id)
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

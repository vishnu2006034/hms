import os
from app import create_app
from hogc.lib import HOGC
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import DeleteRecordRequest, ListRecordsRequest
from app.seed import schema
from app.config import Config
from app.modules.routes_base import _sync_related_record_on_delete

app = create_app()
with app.app_context():
    schema._lookup_module_ids()
    ctx = RequestContext(tenant_id=Config.HOGC_TENANT_ID, org_id=Config.HOGC_ORG_ID, user_id="system", roles=["Admin"])
    
    # Get all visits bypassing RecordRepository
    resp = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.VISITS_MODULE_ID, page=1, page_size=1000))
    visits = resp.items
    print(f"Found {len(visits)} visits to delete.")
    
    for v in visits:
        try:
            old_data = v.data if hasattr(v, 'data') and isinstance(v.data, dict) else {}
            _sync_related_record_on_delete(ctx, schema.VISITS_MODULE_ID, v.id, old_data)
            HOGC.crud.record.delete(DeleteRecordRequest(
                context=ctx, module_id=schema.VISITS_MODULE_ID, record_id=v.id
            ))
            print(f"Deleted visit {v.id}")
        except Exception as e:
            print(f"Error deleting visit {v.id}: {e}")

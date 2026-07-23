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
    
    # Get all patients bypassing RecordRepository
    resp = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=schema.PATIENTS_MODULE_ID, page=1, page_size=1000))
    patients = resp.items
    print(f"Found {len(patients)} patients to delete.")
    
    for p in patients:
        try:
            old_data = p.data if hasattr(p, 'data') and isinstance(p.data, dict) else {}
            _sync_related_record_on_delete(ctx, schema.PATIENTS_MODULE_ID, p.id, old_data)
            HOGC.crud.record.delete(DeleteRecordRequest(
                context=ctx, module_id=schema.PATIENTS_MODULE_ID, record_id=p.id
            ))
            print(f"Deleted patient {p.id}")
        except Exception as e:
            print(f"Error deleting patient {p.id}: {e}")

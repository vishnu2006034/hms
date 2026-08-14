import os
from app import create_app
from hogc.lib.contracts.crud.models import QueryFilter, RecordQuery
from hogc.lib.contracts.crud.requests import QueryRecordsRequest
from hogc.lib.base import RequestContext
from hogc.lib import HOGC
from app.seed import schema
from app.config import Config

app = create_app()
with app.app_context():
    schema._lookup_module_ids()
    ctx = RequestContext(tenant_id=Config.HOGC_TENANT_ID, org_id=Config.HOGC_ORG_ID, user_id="system", roles=["Admin"])
    q = RecordQuery(module_id=schema.PATIENTS_MODULE_ID, filters=[QueryFilter(field="id", operator="in", value=["1", "2"])])
    try:
        resp = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=q))
        print("Success! Items:", len(resp.items))
    except Exception as e:
        print("Error:", e)

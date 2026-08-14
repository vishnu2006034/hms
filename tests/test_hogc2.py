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
    q1 = RecordQuery(module_id=schema.PATIENTS_MODULE_ID, filters=[QueryFilter(field="first_name", operator="eq", value="Rajesh")])
    q2 = RecordQuery(module_id=schema.PATIENTS_MODULE_ID, filters=[QueryFilter(field="first_name", operator="in", value=["Rajesh", "Ananya"])])
    
    try:
        r1 = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=q1))
        print("Q1 Items:", len(r1.items), [i.data.get("first_name") for i in r1.items])
        r2 = HOGC.crud.record.query(QueryRecordsRequest(context=ctx, query=q2))
        print("Q2 Items:", len(r2.items), [i.data.get("first_name") for i in r2.items])
    except Exception as e:
        print("Error:", e)

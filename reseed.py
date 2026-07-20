from app import create_app

app = create_app()
with app.app_context():
    from app.seed.schema import _drop_all_hogc
    from app.seed import _do_seed

    print("Dropping all HOGC data...")
    _drop_all_hogc()

    print("Reseeding from scratch...")
    _do_seed()

    from hogc.lib import HOGC
    from hogc.lib.contracts.crud.requests import ListModulesRequest, ListRecordsRequest
    from app.seed.schema import _ctx

    ctx = _ctx()
    modules = HOGC.crud.module.list(ListModulesRequest(context=ctx, page=1, page_size=50))
    print(f"\nModules: {modules.total}")
    for m in modules.items:
        records = HOGC.crud.record.list(ListRecordsRequest(context=ctx, module_id=m.id, page=1, page_size=100))
        print(f"  {m.api_name}: {records.total} records")
    print("\nDone!")

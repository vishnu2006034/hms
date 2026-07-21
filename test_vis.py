from app import create_app
from flask_login import current_user
from app.services.visibility_service import VisibilityService
from app.modules.routes_base import _check_access
from hogc.lib.base import RequestContext
from app.config import Config

class MockUser:
    def __init__(self, role, hogc_record_id):
        self.role = role
        self.hogc_record_id = hogc_record_id
        self.id = 1
        self.is_authenticated = True

app = create_app()

with app.app_context():
    import flask_login
    # mock current_user as a global override for the test
    mock_user = MockUser("Doctor", "dummy")
    
    # We patch _ctx
    import app.modules.routes_base
    app.modules.routes_base._ctx = lambda: RequestContext(
        tenant_id=Config.HOGC_TENANT_ID, org_id=Config.HOGC_ORG_ID,
        user_id="1", roles=["Doctor"]
    )
    import app.services.visibility_service
    # We also patch current_user used in modules
    flask_login.current_user = mock_user
    app.services.visibility_service.current_user = mock_user
    app.modules.routes_base.current_user = mock_user

    from app.seed import schema
    from hogc.lib import HOGC
    from hogc.lib.contracts.crud.requests import ListRecordsRequest
    
    users = HOGC.crud.record.list(ListRecordsRequest(
        context=app.modules.routes_base._ctx(), module_id=schema.USERS_MODULE_ID, page=1, page_size=10
    )).items
    doctor_id = None
    for u in users:
        if u.data.get("role") == "Doctor":
            doctor_id = u.id
            break
            
    if doctor_id:
        mock_user.hogc_record_id = doctor_id
        res = VisibilityService.get_patients()
        print(f"Total patients for real doctor {doctor_id}: {res.total}")
        for p in res.items:
            print(f"Patient {p.id}")
            assigned = p.data.get("assigned_doctor")
            print(f"  assigned_doctor: {repr(assigned)}")
            print(f"  doctor_id: {repr(doctor_id)}")
            print(f"  _check_access: {_check_access(p, 'assigned_doctor')}")

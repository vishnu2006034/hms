from app import create_app
from app.extensions import db
from hogc.lib import HOGC
from app.services.visibility_service import VisibilityService
from flask_login import current_user

class MockUser:
    def __init__(self, role, hogc_record_id):
        self.role = role
        self.hogc_record_id = hogc_record_id
        self.id = 1
        self.is_authenticated = True

app = create_app()

with app.app_context():
    # Mock current_user
    import flask_login
    flask_login.current_user = MockUser("Doctor", "nonexistent_id")
    
    print("Testing get_patients as Doctor with nonexistent ID...")
    res = VisibilityService.get_patients()
    print(f"Total patients: {res.total}")
    
    print("Testing get_patients as Doctor with existing ID...")
    # Find a real doctor ID
    from app.seed import schema
    from hogc.lib.contracts.crud.requests import ListRecordsRequest
    from app.modules.routes_base import _ctx
    
    ctx = _ctx()
    users = HOGC.crud.record.list(ListRecordsRequest(
        context=ctx, module_id=schema.USERS_MODULE_ID, page=1, page_size=10
    )).items
    doctor_id = None
    for u in users:
        if u.data.get("role") == "Doctor":
            doctor_id = u.id
            break
            
    if doctor_id:
        flask_login.current_user = MockUser("Doctor", doctor_id)
        res = VisibilityService.get_patients()
        print(f"Total patients for real doctor {doctor_id}: {res.total}")
    else:
        print("No doctor found to test.")

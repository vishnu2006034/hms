from flask import render_template
from flask_login import login_required, current_user
from app.main import main_bp
from app.extensions import crud
from app.config import Config
from hogc.lib.base import RequestContext
from hogc.lib.contracts.crud.requests import ListRecordsRequest
import app.modules.seed as seed


def _get_ctx():
    return RequestContext(
        tenant_id=Config.HOGC_TENANT_ID,
        org_id=Config.HOGC_ORG_ID,
        user_id=str(current_user.id),
        roles=[current_user.role],
    )


@main_bp.route("/")
@login_required
def dashboard():
    ctx = _get_ctx()
    stats = {"patients": 0, "visits": 0, "inventory": 0, "lab": 0, "prescriptions": 0}

    try:
        patients = crud.records.list_records(ListRecordsRequest(
            context=ctx, module_id=seed.PATIENTS_MODULE_ID, page=1, page_size=1
        ))
        stats["patients"] = patients.total

        visits = crud.records.list_records(ListRecordsRequest(
            context=ctx, module_id=seed.VISITS_MODULE_ID, page=1, page_size=1
        ))
        stats["visits"] = visits.total

        inventory = crud.records.list_records(ListRecordsRequest(
            context=ctx, module_id=seed.INVENTORY_MODULE_ID, page=1, page_size=1
        ))
        stats["inventory"] = inventory.total

        prescriptions = crud.records.list_records(ListRecordsRequest(
            context=ctx, module_id=seed.PRESCRIPTIONS_MODULE_ID, page=1, page_size=1
        ))
        stats["prescriptions"] = prescriptions.total

        lab = crud.records.list_records(ListRecordsRequest(
            context=ctx, module_id=seed.LABORATORY_MODULE_ID, page=1, page_size=1
        ))
        stats["lab"] = lab.total
    except Exception:
        pass

    return render_template("main/dashboard.html", stats=stats)
